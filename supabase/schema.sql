-- Schema for FabulA. All tables are prefixed gm_ so they do not
-- clash with older tables (players, game_state). Each row holds one record as JSONB
-- in `data`, plus index columns and a version for optimistic locking.
-- Run in the Supabase SQL editor. The server uses the service role key (bypasses RLS).

create table if not exists gm_players (
  id text primary key, data jsonb not null, version int not null default 1,
  updated_at timestamptz not null default now());

create table if not exists gm_adventures (
  id text primary key, data jsonb not null, version int not null default 1,
  owner_player_id text, updated_at timestamptz not null default now());

create table if not exists gm_npcs (
  id text primary key, data jsonb not null, version int not null default 1,
  adventure_id text, game_id text, updated_at timestamptz not null default now());

create table if not exists gm_locations (
  id text primary key, data jsonb not null, version int not null default 1,
  adventure_id text, game_id text, updated_at timestamptz not null default now());

create table if not exists gm_games (
  id text primary key, data jsonb not null, version int not null default 1,
  phase text, turn_closes timestamptz, updated_at timestamptz not null default now());

create table if not exists gm_characters (
  id text primary key, data jsonb not null, version int not null default 1,
  game_id text not null, player_id text not null, is_alive boolean not null default true,
  updated_at timestamptz not null default now());

create table if not exists gm_npc_states (
  id text primary key, data jsonb not null, version int not null default 1,
  game_id text not null, updated_at timestamptz not null default now());

create table if not exists gm_location_states (
  id text primary key, data jsonb not null, version int not null default 1,
  game_id text not null, updated_at timestamptz not null default now());

create table if not exists gm_submit_actions (
  id text primary key, data jsonb not null, version int not null default 1,
  game_id text not null, turn int not null, updated_at timestamptz not null default now());

create table if not exists gm_tasks (
  id text primary key, data jsonb not null, version int not null default 1,
  player_id text not null, status text not null default 'open', updated_at timestamptz not null default now());

create index if not exists gm_tasks_player on gm_tasks (player_id, status);
create index if not exists gm_characters_game on gm_characters (game_id);
create index if not exists gm_characters_player on gm_characters (player_id);
create index if not exists gm_npc_states_game on gm_npc_states (game_id);
create index if not exists gm_location_states_game on gm_location_states (game_id);
create index if not exists gm_submit_actions_game on gm_submit_actions (game_id, turn);
create index if not exists gm_games_due on gm_games (phase, turn_closes);

alter table gm_players enable row level security;
alter table gm_adventures enable row level security;
alter table gm_npcs enable row level security;
alter table gm_locations enable row level security;
alter table gm_games enable row level security;
alter table gm_characters enable row level security;
alter table gm_npc_states enable row level security;
alter table gm_location_states enable row level security;
alter table gm_submit_actions enable row level security;
alter table gm_tasks enable row level security;
-- No policies: only the service role (the MCP server) can read or write.

-- Secret player keys. The key itself is never stored: the row id is its SHA-256 hash and `data` holds the player id.
create table if not exists gm_keys (
  id text primary key, data jsonb not null, version int not null default 1,
  player_id text, updated_at timestamptz not null default now());
alter table gm_keys enable row level security;

-- Counters of AI Master requests per tier and day, to stay inside the provider's free-tier quotas.
create table if not exists gm_usage (
  id text primary key, data jsonb not null, version int not null default 1,
  updated_at timestamptz not null default now());
alter table gm_usage enable row level security;

-- Illustrations. The records say who may see a picture; the pictures themselves are in a PRIVATE storage bucket and are reached
-- only through short-lived signed links made by the server.
create table if not exists gm_images (
  id text primary key, data jsonb not null, version int not null default 1,
  game_id text not null, status text, updated_at timestamptz not null default now());
alter table gm_images enable row level security;
insert into storage.buckets (id, name, public) values ('gm-images', 'gm-images', false) on conflict (id) do nothing;

-- Imported rulesets. A player's client converts a document into the ruleset format; it stays 'pending' until the host approves it.
create table if not exists gm_rulesets (
  id text primary key, data jsonb not null, version int not null default 1,
  status text, updated_at timestamptz not null default now());
alter table gm_rulesets enable row level security;

-- Atomic commit (TLR-06-009). The server sends every record a request changed in one call; they are all written or none are.
-- Each item: {table, id, version, data, index}. version 0 = insert; otherwise update only if the stored version still matches,
-- else the whole call fails with 'conflict:' and nothing is written. Returns the new versions in order.
-- Index columns are the table's own columns named in `index` (phase, game_id, ...). Run again any time: it is idempotent.
create or replace function gm_commit(batch jsonb) returns jsonb
language plpgsql as $$
declare
  item jsonb; tbl text; rid text; ver int; idx jsonb; dat jsonb; cols text; sets text; n int; out jsonb := '[]'::jsonb;
begin
  for item in select * from jsonb_array_elements(batch) loop
    tbl := item->>'table'; rid := item->>'id'; ver := (item->>'version')::int;
    dat := item->'data'; idx := coalesce(item->'index', '{}'::jsonb);
    if tbl !~ '^gm_[a-z_]+$' or to_regclass('public.' || quote_ident(tbl)) is null then
      raise exception 'bad table %', tbl;
    end if;
    if ver = 0 then
      idx := idx || jsonb_build_object('id', rid, 'data', dat, 'version', 1, 'updated_at', now());
      select string_agg(format('%I', k), ', ') into cols from jsonb_object_keys(idx) k;
      begin
        execute format('insert into %I (%s) select %s from jsonb_populate_record(null::%I, $1)', tbl, cols, cols, tbl) using idx;
      exception when unique_violation then
        raise exception 'conflict: % % already exists', tbl, rid;
      end;
      out := out || to_jsonb(1);
    else
      idx := idx || jsonb_build_object('data', dat, 'version', ver + 1, 'updated_at', now());
      select string_agg(format('%I = r.%I', k, k), ', ') into sets from jsonb_object_keys(idx) k;
      execute format('update %I t set %s from jsonb_populate_record(null::%I, $1) r where t.id = $2 and t.version = $3', tbl, sets, tbl)
        using idx, rid, ver;
      get diagnostics n = row_count;
      if n = 0 then
        raise exception 'conflict: % % changed', tbl, rid;
      end if;
      out := out || to_jsonb(ver + 1);
    end if;
  end loop;
  return out;
end $$;
revoke all on function gm_commit(jsonb) from public, anon, authenticated;
grant execute on function gm_commit(jsonb) to service_role;

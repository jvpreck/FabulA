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
  phase text, tick_closes timestamptz, updated_at timestamptz not null default now());

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
  game_id text not null, tick int not null, updated_at timestamptz not null default now());

create table if not exists gm_tasks (
  id text primary key, data jsonb not null, version int not null default 1,
  player_id text not null, status text not null default 'open', updated_at timestamptz not null default now());

create index if not exists gm_tasks_player on gm_tasks (player_id, status);
create index if not exists gm_characters_game on gm_characters (game_id);
create index if not exists gm_characters_player on gm_characters (player_id);
create index if not exists gm_npc_states_game on gm_npc_states (game_id);
create index if not exists gm_location_states_game on gm_location_states (game_id);
create index if not exists gm_submit_actions_game on gm_submit_actions (game_id, tick);
create index if not exists gm_games_due on gm_games (phase, tick_closes);

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

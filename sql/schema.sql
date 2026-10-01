create extension if not exists pgcrypto;
create schema if not exists pinhook;
create table if not exists pinhook.source_files (
 id uuid primary key default gen_random_uuid(), source_name text not null, source_url text,
 retrieved_at timestamptz not null default now(), sha256 text, format text,
 coverage text, license_note text, raw_storage_path text, parser_version text,
 unique(source_name, sha256)
);
create table if not exists pinhook.horses (
 id uuid primary key default gen_random_uuid(), registry text, registration_number text,
 foaling_year integer, foaling_date date, horse_name text, sex text, color text,
 sire_name text, sire_registry_number text, dam_name text, dam_registry_number text,
 damsire_name text, breeder text, country_of_foaling text,
 created_at timestamptz not null default now(),
 unique(registry, registration_number)
);
create table if not exists pinhook.sales (
 id uuid primary key default gen_random_uuid(), auction_house text not null,
 sale_code text not null, sale_name text not null, sale_type text not null,
 first_date date, last_date date, location text, source_url text,
 unique(auction_house, sale_code)
);
create table if not exists pinhook.sale_entries (
 id uuid primary key default gen_random_uuid(), sale_id uuid not null references pinhook.sales,
 horse_id uuid references pinhook.horses, source_file_id uuid references pinhook.source_files,
 source_entry_id text, hip text not null, session_date date,
 name_as_cataloged text, sire_as_cataloged text, dam_as_cataloged text,
 foaling_year_as_cataloged integer, sex_as_cataloged text, breeder_as_cataloged text,
 consignor text, buyer text, status text not null default 'unknown'
 check (status in ('sold','rna','out','withdrawn','entered_not_sold','unknown')),
 price_usd numeric(14,2), currency text default 'USD',
 reported_bid_usd numeric(14,2), status_evidence text, source_url text,
 raw_record jsonb not null default '{}'::jsonb, ingested_at timestamptz not null default now(),
 unique(sale_id, hip), unique(sale_id, source_entry_id),
 check (price_usd is null or price_usd >= 0),
 check (status <> 'sold' or price_usd is not null)
);
create index if not exists sale_entries_horse_idx on pinhook.sale_entries(horse_id);
create index if not exists sale_entries_pedigree_idx on pinhook.sale_entries(lower(sire_as_cataloged),lower(dam_as_cataloged),foaling_year_as_cataloged);
create table if not exists pinhook.horse_identity_matches (
 id uuid primary key default gen_random_uuid(), left_entry_id uuid not null references pinhook.sale_entries,
 right_entry_id uuid not null references pinhook.sale_entries,
 horse_id uuid references pinhook.horses, method text not null, confidence numeric(5,4),
 evidence jsonb not null default '{}'::jsonb,
 decision text not null check(decision in ('accepted','rejected','review')),
 reviewer text, reviewed_at timestamptz, created_at timestamptz not null default now(),
 unique(left_entry_id,right_entry_id), check(left_entry_id <> right_entry_id)
);
create table if not exists pinhook.races (
 id uuid primary key default gen_random_uuid(), provider text not null, provider_race_id text,
 track_code text, race_date date not null, race_number integer,
 race_name text, race_type text, stakes_flag boolean, graded_level text,
 purse_usd numeric(14,2), jurisdiction text, source_file_id uuid references pinhook.source_files,
 source_url text, raw_record jsonb not null default '{}'::jsonb,
 unique(provider,provider_race_id)
);
create table if not exists pinhook.race_results (
 id uuid primary key default gen_random_uuid(), race_id uuid not null references pinhook.races,
 horse_id uuid references pinhook.horses, provider_horse_id text, horse_name text not null,
 finish_position integer, official_winner boolean, earnings_usd numeric(14,2),
 disqualified boolean, source_file_id uuid references pinhook.source_files,
 raw_record jsonb not null default '{}'::jsonb,
 unique(race_id,provider_horse_id)
);
create index if not exists race_results_horse_idx on pinhook.race_results(horse_id);
create table if not exists pinhook.pinhook_cohort (
 yearling_entry_id uuid primary key references pinhook.sale_entries,
 selected_two_year_old_entry_id uuid references pinhook.sale_entries,
 outcome text not null check(outcome in ('sold_at_2yo','rna_at_2yo','out_at_2yo','entered_not_sold_at_2yo','no_2yo_sale_identified','unresolved')),
 outcome_scope text not null default 'target_sales_only',
 yearling_price_usd numeric(14,2), two_year_old_price_usd numeric(14,2),
 price_appreciation_usd numeric(14,2) generated always as (two_year_old_price_usd-yearling_price_usd) stored,
 gross_return_pct numeric(14,4) generated always as
 (case when yearling_price_usd > 0 and two_year_old_price_usd is not null
 then 100*(two_year_old_price_usd/yearling_price_usd-1) end) stored,
 days_between_transactions integer, match_id uuid references pinhook.horse_identity_matches,
 observed_until date, adjudication_note text, updated_at timestamptz not null default now(),
 check(selected_two_year_old_entry_id is distinct from yearling_entry_id)
);
-- Keep every subsequent offering in sale_entries; selected_two_year_old_entry_id is the first
-- confirmed qualifying 2YO offering. An RNA followed by sale must remain visible in the event history.
-- No direct partner access to source_files/raw_record until source licensing and RLS are set.

-- ─────────────────────────────────────────────────────────────────────────────
-- Etlyx Apply — Supabase Schema
-- Run this in: Supabase Dashboard → SQL Editor → New query → Run
-- ─────────────────────────────────────────────────────────────────────────────

-- Profiles table (one row per user, created automatically on signup)
create table if not exists public.profiles (
  id                 uuid references auth.users(id) on delete cascade primary key,
  email              text,
  plan               text not null default 'free',   -- 'free' | 'pro'
  stripe_customer_id text,
  stripe_sub_id      text,
  searches_used      integer not null default 0,
  searches_reset_at  timestamptz,
  created_at         timestamptz not null default now()
);

-- Row Level Security: users can only read/update their own profile
alter table public.profiles enable row level security;

create policy "Users can view own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id);

-- Auto-create a profile row when a new user signs up
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  return new;
end;
$$ language plpgsql security definer;

-- Drop the trigger if it already exists, then recreate
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

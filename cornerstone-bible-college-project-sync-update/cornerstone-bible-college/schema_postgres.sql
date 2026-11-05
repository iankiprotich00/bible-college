-- Cornerstone Bible College: login database for Postgres / Supabase.
-- NOT tested here. Same design as schema.sql. In Supabase, passwords live in the built-in
-- auth.users table (hashed for you), so this schema keeps profiles and the login record only.

create table profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  role        text not null check (role in ('student','tutor','admin')),
  full_name   text not null,
  status      text not null default 'active' check (status in ('active','suspended','pending')),
  created_at  timestamptz not null default now()
);

create table students (
  user_id             uuid primary key references profiles(id) on delete cascade,
  id_number           text not null unique,
  registration_number text not null unique,
  year_of_study       int  not null default 1 check (year_of_study between 1 and 4)
);

create table tutors (
  user_id      uuid primary key references profiles(id) on delete cascade,
  staff_number text unique
);

create table courses (
  code    text primary key,
  title   text not null,
  credits int  not null
);

create table tutor_courses (
  tutor_id    uuid not null references tutors(user_id) on delete cascade,
  course_code text not null references courses(code),
  primary key (tutor_id, course_code)
);

create table login_events (
  id         bigint generated always as identity primary key,
  user_id    uuid references profiles(id) on delete set null,
  portal     text not null check (portal in ('student','tutor')),
  method     text not null check (method in ('email','id_number','registration_number')),
  identifier text not null,
  success    boolean not null,
  reason     text,
  ip_address inet,
  user_agent text,
  created_at timestamptz not null default now()
);
create index on login_events (user_id, created_at);
create index on login_events (created_at);

-- Row level security: people see only their own rows; staff tools use the service key.
alter table profiles     enable row level security;
alter table students     enable row level security;
alter table tutors       enable row level security;
alter table login_events enable row level security;

create policy "own profile"  on profiles     for select using (id = auth.uid());
create policy "own student"  on students     for select using (user_id = auth.uid());
create policy "own tutor"    on tutors       for select using (user_id = auth.uid());
create policy "own logins"   on login_events for select using (user_id = auth.uid());
-- Inserts into login_events should come from your server (service key), not from the browser.

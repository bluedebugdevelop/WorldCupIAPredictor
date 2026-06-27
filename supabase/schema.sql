-- Esquema de Supabase para WorldCupIAPredictor.
-- Ejecuta esto en el SQL Editor de tu proyecto Supabase (una sola vez).
--
-- Guardamos el estado en vivo (designaciones de árbitros y árbitros descubiertos)
-- como un único blob JSON bajo la clave 'live'. El backend lo lee/escribe con la
-- service_role key (que se salta la RLS), así que no hacen falta políticas.

create table if not exists public.kv_store (
  key        text primary key,
  value      jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

insert into public.kv_store (key, value)
values ('live', '{"updated": null, "appointments": {}, "referees": {}}'::jsonb)
on conflict (key) do nothing;

-- RLS activada: nadie accede con la anon key; solo el backend con service_role.
alter table public.kv_store enable row level security;

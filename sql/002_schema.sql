-- Core multi-tenant entities
create table if not exists tenants (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  external_tenant_id text,
  created_at timestamptz default now()
);

create table if not exists domains (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  domain_name text not null,
  provider text check (provider in ('m365','gmail')) default 'm365',
  unique (tenant_id, domain_name)
);

create table if not exists mailboxes (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  domain_id uuid references domains(id) on delete set null,
  user_principal_name text not null,
  display_name text,
  provider_id text,
  unique (tenant_id, user_principal_name)
);

create table if not exists threads (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  mailbox_id uuid references mailboxes(id) on delete cascade,
  thread_key text,
  subject text,
  first_message_at timestamptz,
  last_message_at timestamptz,
  participants jsonb,
  unique (tenant_id, mailbox_id, thread_key)
);

create table if not exists emails (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  mailbox_id uuid references mailboxes(id) on delete cascade,
  thread_id uuid references threads(id) on delete cascade,
  provider_message_id text,
  from_address text,
  to_addresses text[],
  cc_addresses text[],
  bcc_addresses text[],
  sent_at timestamptz,
  received_at timestamptz,
  subject text,
  body_text text,
  body_html text,
  language_detected text,
  importance text,
  category text,
  labels text[],
  has_attachments boolean default false,
  in_reply_to text,
  created_at timestamptz default now(),
  unique (tenant_id, mailbox_id, provider_message_id)
);

-- Embeddings for email chunks
create table if not exists email_embeddings (
  id bigserial primary key,
  email_id uuid references emails(id) on delete cascade,
  tenant_id uuid references tenants(id) on delete cascade,
  chunk_index int default 0,
  content_snippet text,
  embedding vector(1536)  -- default dim for text-embedding-3-small
);
create index if not exists idx_email_embeddings_tenant on email_embeddings(tenant_id);
create index if not exists idx_email_embeddings_vector on email_embeddings using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Knowledge Base (your custom materials)
create table if not exists kb_documents (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  title text,
  source text, -- filename/url/category
  mime_type text,
  created_at timestamptz default now()
);

create table if not exists kb_chunks (
  id bigserial primary key,
  doc_id uuid references kb_documents(id) on delete cascade,
  tenant_id uuid references tenants(id) on delete cascade,
  chunk_index int,
  content text,
  embedding vector(1536)
);
create index if not exists idx_kb_chunks_tenant on kb_chunks(tenant_id);
create index if not exists idx_kb_chunks_vector on kb_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- Assistant memory & tasks (personal assistant features)
create table if not exists user_profiles (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  upn text not null,
  display_name text,
  preferences jsonb default '{}'::jsonb,
  unique (tenant_id, upn)
);

create table if not exists assistant_memory (
  id bigserial primary key,
  tenant_id uuid references tenants(id) on delete cascade,
  upn text not null,
  key text not null,
  value text,
  created_at timestamptz default now()
);

create table if not exists tasks (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  upn text not null,
  title text not null,
  due_at timestamptz,
  priority text check (priority in ('low','medium','high')) default 'medium',
  status text check (status in ('open','done','archived')) default 'open',
  source text,   -- 'email:<id>', 'kb:<id>', 'manual'
  created_at timestamptz default now()
);

-- Helpful indexes
create index if not exists idx_emails_tenant_time on emails(tenant_id, received_at desc);
create index if not exists idx_threads_tenant_time on threads(tenant_id, last_message_at desc);
create index if not exists idx_kb_docs_tenant on kb_documents(tenant_id);
create index if not exists idx_tasks_user on tasks(tenant_id, upn, status);

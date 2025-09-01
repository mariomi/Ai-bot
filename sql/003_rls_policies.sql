alter table tenants enable row level security;
alter table domains enable row level security;
alter table mailboxes enable row level security;
alter table threads enable row level security;
alter table emails enable row level security;
alter table email_embeddings enable row level security;
alter table kb_documents enable row level security;
alter table kb_chunks enable row level security;
alter table user_profiles enable row level security;
alter table assistant_memory enable row level security;
alter table tasks enable row level security;

-- NOTE: App must set SET app.tenant_id = '<TENANT_UUID>' per connection.
create policy "tenant_select_tenants" on tenants for select using (true);

create policy "tenant_isolation_domains" on domains
  for all using (tenant_id::text = current_setting('app.tenant_id', true))
  with check (tenant_id::text = current_setting('app.tenant_id', true));

create policy "tenant_isolation_mailboxes" on mailboxes
  for all using (tenant_id::text = current_setting('app.tenant_id', true))
  with check (tenant_id::text = current_setting('app.tenant_id', true));

create policy "tenant_isolation_threads" on threads
  for all using (tenant_id::text = current_setting('app.tenant_id', true))
  with check (tenant_id::text = current_setting('app.tenant_id', true));

create policy "tenant_isolation_emails" on emails
  for all using (tenant_id::text = current_setting('app.tenant_id', true))
  with check (tenant_id::text = current_setting('app.tenant_id', true));

create policy "tenant_isolation_email_embeddings" on email_embeddings
  for all using (tenant_id::text = current_setting('app.tenant_id', true))
  with check (tenant_id::text = current_setting('app.tenant_id', true));

create policy "tenant_isolation_kb_docs" on kb_documents
  for all using (tenant_id::text = current_setting('app.tenant_id', true))
  with check (tenant_id::text = current_setting('app.tenant_id', true));

create policy "tenant_isolation_kb_chunks" on kb_chunks
  for all using (tenant_id::text = current_setting('app.tenant_id', true))
  with check (tenant_id::text = current_setting('app.tenant_id', true));

create policy "tenant_isolation_profiles" on user_profiles
  for all using (tenant_id::text = current_setting('app.tenant_id', true))
  with check (tenant_id::text = current_setting('app.tenant_id', true));

create policy "tenant_isolation_memory" on assistant_memory
  for all using (tenant_id::text = current_setting('app.tenant_id', true))
  with check (tenant_id::text = current_setting('app.tenant_id', true));

create policy "tenant_isolation_tasks" on tasks
  for all using (tenant_id::text = current_setting('app.tenant_id', true))
  with check (tenant_id::text = current_setting('app.tenant_id', true));

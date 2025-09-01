-- Semantic search over emails: returns best K chunks joined with emails
create or replace function semantic_search_emails(tenant_in uuid, query_vec vector, k int)
returns table (
  email_id uuid,
  from_address text,
  subject text,
  body_text text,
  received_at timestamptz,
  snippet text,
  distance float
) language sql stable as $$
  select e.id as email_id,
         e.from_address,
         e.subject,
         e.body_text,
         e.received_at,
         left(ee.content_snippet, 1000) as snippet,
         (ee.embedding <-> query_vec) as distance
  from email_embeddings ee
  join emails e on e.id = ee.email_id
  where ee.tenant_id = tenant_in
  order by ee.embedding <-> query_vec
  limit k
$$;

-- Semantic search over KB chunks
create or replace function semantic_search_kb(tenant_in uuid, query_vec vector, k int)
returns table (
  doc_id uuid,
  title text,
  content text,
  distance float
) language sql stable as $$
  select d.id as doc_id,
         d.title,
         c.content,
         (c.embedding <-> query_vec) as distance
  from kb_chunks c
  join kb_documents d on d.id = c.doc_id
  where c.tenant_id = tenant_in
  order by c.embedding <-> query_vec
  limit k
$$;

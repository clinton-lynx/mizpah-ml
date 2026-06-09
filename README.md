# Mizpah ML Service

This is the machine learning module for the Mizpah AI Vision Safety Platform. It exposes a fast API for face embedding extraction and vector matching against a Supabase database.

---

## 🚀 API Contract for Backend Integration

**Base URL:** `https://mizpah-ml-production.up.railway.app`

### 1. Scan Endpoint
**Endpoint:** `POST /scan`  
**Description:** Takes a cropped face image, runs it against the Supabase database using pgvector, and returns the best match.

**Request Body:**
```json
{
  "image": "<base64_encoded_string_of_the_cropped_face>",
  "mode": "passive" 
}
```
*(Note: `mode` can be "passive" for continuous security/missing persons surveillance, or "active" for targeted medical emergencies).*

**Response (If match found):**
```json
{
  "matched": true,
  "confidence": 98.5,
  "profile": {
    "name": "John Doe",
    "type": "medical",
    "blood_type": "O+",
    "allergies": ["Penicillin", "Peanuts"],
    "conditions": ["Asthma"],
    "emergency_contact": "+1234567890"
  }
}
```

**Response (If no match):**
```json
{
  "matched": false,
  "confidence": 45.2,
  "profile": null
}
```

---

### 2. Enroll Endpoint
**Endpoint:** `POST /enroll`  
**Description:** Takes a clear face image during registration, generates an embedding, and stores it in the database.

**Request Body:**
```json
{
  "image": "<base64_encoded_string_of_the_face>",
  "person_id": "<uuid-of-the-person-record-in-supabase>",
  "type": "medical"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Face enrolled successfully.",
  "embedding_id": "<uuid-of-the-vector-record>"
}
```

---

## 🚂 Deployment via Railway CLI

If you need to push code updates to Railway without using GitHub, you can use the Railway CLI from your terminal.

**Prerequisites:**
You must have the Railway CLI installed. If not, install it via NPM:
```bash
npm install -g @railway/cli
```

**Deployment Steps:**
1. Open your terminal in this `mizpah-ml` folder.
2. Log into your Railway account:
   ```bash
   railway login
   ```
3. Push your local code directly to the Railway servers:
   ```bash
   railway up
   ```
4. Wait a few moments for the build to finish. Once completed, your live URL will be active.

### 🛠️ Useful Railway Commands

Here are the most common commands you will need when managing your deployment:

| Command | Description |
|---|---|
| `railway up` | **Deploy your code**. Pushes your current local files to the Railway server. |
| `railway domain` | **Get your URL**. Generates and displays your live public API URL. |
| `railway logs` | **View live logs**. Streams the server logs so you can see print statements or errors. |
| `railway redeploy` | **Force a redeploy**. Restarts your service and triggers a fresh build. |
| `railway env` | **View environment variables**. Shows the secrets (like Supabase keys) configured on Railway. |

---

## 🗄️ Supabase Database Setup (For Backend Dev)

For the ML module to correctly perform face matching, the Supabase database must be set up with `pgvector` and an RPC function named `match_face`.

**Run this exact SQL in the Supabase SQL Editor:**

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE OR REPLACE FUNCTION match_face (
  query_embedding vector(512),
  match_threshold float,
  match_count int,
  search_mode text
)
RETURNS TABLE (
  id uuid,
  person_id uuid,
  name text,
  type text,
  blood_type text,
  allergies text[],
  conditions text[],
  emergency_contact text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    face_vectors.id,
    face_vectors.person_id,
    face_vectors.name,
    face_vectors.type,
    face_vectors.blood_type,
    face_vectors.allergies,
    face_vectors.conditions,
    face_vectors.emergency_contact,
    1 - (face_vectors.embedding <=> query_embedding) AS similarity
  FROM face_vectors
  WHERE face_vectors.type = search_mode
    AND 1 - (face_vectors.embedding <=> query_embedding) > match_threshold
  ORDER BY face_vectors.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```



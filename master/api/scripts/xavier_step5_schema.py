"""Step 5.2b: Get Worker OpenAPI schema + retry with correct format."""
import json
import urllib.request

WORKER = "http://192.168.1.200:8000"

def get_raw(url, timeout=10):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode()

# Get full OpenAPI spec
spec = json.loads(get_raw(f"{WORKER}/openapi.json"))

print("=" * 60)
print("WORKER OPENAPI SCHEMA")
print("=" * 60)

# Print each endpoint with full schema
for path, methods in spec.get("paths", {}).items():
    for method, details in methods.items():
        print(f"\n{method.upper()} {path}")
        print(f"  Summary: {details.get('summary', 'N/A')}")
        if "requestBody" in details:
            rb = details["requestBody"]
            print(f"  Request Body:")
            for ct, schema_info in rb.get("content", {}).items():
                print(f"    Content-Type: {ct}")
                ref = schema_info.get("schema", {})
                if "$ref" in ref:
                    ref_name = ref["$ref"].split("/")[-1]
                    full_schema = spec.get("components", {}).get("schemas", {}).get(ref_name, {})
                    print(f"    Schema ({ref_name}):")
                    print(f"    {json.dumps(full_schema, indent=4)[:800]}")
                else:
                    print(f"    Schema: {json.dumps(ref, indent=4)[:800]}")
        if "responses" in details:
            for code, resp_info in details["responses"].items():
                print(f"  Response {code}: {resp_info.get('description', '')}")

# Print all schemas
print("\n" + "=" * 60)
print("ALL SCHEMAS")
print("=" * 60)
for name, schema in spec.get("components", {}).get("schemas", {}).items():
    print(f"\n{name}:")
    print(json.dumps(schema, indent=2)[:600])

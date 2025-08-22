# Static Questions Endpoint Documentation

## Overview

The questions endpoint provides static assessment questions in a standardized format for the CVP Lite application. This endpoint returns predefined questions with proper structure including translations, metadata, and pagination support. No user validation or dynamic generation is performed.

## Endpoint Details

- **URL**: `/cvp_lite/questions`
- **Method**: `POST`
- **Content-Type**: `application/json`

## Request Format

```json
{
  "student_id": "string",
  "page": 1,
  "page_size": 10,
  "category_id": "string (optional)"
}
```

### Request Parameters

| Parameter     | Type    | Required | Description                                         |
| ------------- | ------- | -------- | --------------------------------------------------- |
| `student_id`  | string  | Yes      | Student identifier (any value accepted)             |
| `page`        | integer | No       | Page number for pagination (default: 1)             |
| `page_size`   | integer | No       | Number of questions per page (default: 10)          |
| `category_id` | string  | No       | Filter questions by category (e.g., "riasec", "mi") |

## Response Format

The endpoint returns questions in the following structure:

```json
{
  "data": [
    {
      "id": "uuid",
      "text": "Question text",
      "type": "single_choice",
      "options": [
        {
          "id": "option_id",
          "label": "Option text",
          "label_translations": {
            "hi": "Hindi translation",
            "en": "English text"
          }
        }
      ],
      "required": true,
      "category_id": "riasec",
      "weight": 1.5,
      "lang": "en-IN",
      "created_at": "2025-08-21T07:15:00Z",
      "order": 1
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 10,
    "total": 2,
    "assessment": {
      "id": "uuid",
      "step_type": "interests_strengths",
      "title": "Interest & Strengths Discovery",
      "scientific_basis": "riasec",
      "generated_at": "2025-08-21T07:15:00Z",
      "categories": [
        {
          "id": "riasec",
          "name": "RIASEC Assessment",
          "description": "Holland's RIASEC model assessment",
          "theory": "Holland's RIASEC Model",
          "weight": 1.5
        }
      ]
    }
  },
  "links": {
    "self": "https://api.example.com/v1/questions?page=1&page_size=10",
    "next": null,
    "prev": null
  }
}
```

## Response Fields

### Data Array

Each question object contains:

- `id`: Unique identifier for the question
- `text`: The question text
- `type`: Question type (currently "single_choice")
- `options`: Array of answer options with translations
- `required`: Whether the question is required
- `category_id`: Assessment category (e.g., "riasec", "mi")
- `weight`: Question weight for scoring
- `lang`: Language code (e.g., "en-IN")
- `created_at`: ISO timestamp when question was created
- `order`: Question order in the sequence

### Meta Object

Contains pagination and assessment metadata:

- `page`: Current page number
- `page_size`: Number of items per page
- `total`: Total number of questions
- `assessment`: Assessment metadata including categories

### Links Object

Contains pagination links:

- `self`: Current page URL
- `next`: Next page URL (null if no next page)
- `prev`: Previous page URL (null if no previous page)

## Example Usage

### cURL Example

```bash
curl -X POST "http://localhost:8001/cvp_lite/questions" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student123",
    "page": 1,
    "page_size": 5
  }'
```

### Python Example

```python
import requests

url = "http://localhost:8001/cvp_lite/questions"
data = {
    "student_id": "student123",
    "page": 1,
    "page_size": 5
}

response = requests.post(url, json=data)
questions = response.json()
print(f"Retrieved {len(questions['data'])} questions")
```

## Error Responses

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

## Notes

- This is a static endpoint that returns predefined questions
- No user validation or database queries are performed
- Questions include proper Hindi and English translations
- The endpoint supports pagination parameters (though currently returns static data)
- Questions are categorized by assessment type (RIASEC, Multiple Intelligences, etc.)
- Each question has a weight that can be used for scoring calculations

## Testing

You can test the endpoint using the provided test script:

```bash
python test_questions_endpoint.py
```

Make sure the server is running on `localhost:8001` before running the test.

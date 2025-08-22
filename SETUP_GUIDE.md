# PDF Recipe Upload Setup Guide

This guide will help you set up the system to upload recipes from PDF files to Pinecone database.

## Prerequisites

1. **Python 3.8+** installed on your system
2. **Pinecone API Key** - Get from [Pinecone Console](https://app.pinecone.io/)
3. **OpenAI API Key** - Get from [OpenAI Platform](https://platform.openai.com/)
4. **MongoDB Connection String** (optional, for user management)

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

1. Copy the environment template:

```bash
cp env.example .env
```

2. Edit `.env` file with your API keys:

```env
PINECONE_API_KEY=your_pinecone_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
MONGODB_URI=your_mongodb_connection_string_here
PINECONE_INDEX_NAME=recipes-db
```

## Step 3: Create Sample PDF for Testing

Run the sample PDF creation script:

```bash
python create_sample_pdf.py
```

This will create a `pdf_recipes/sample_recipes.pdf` file with 3 sample recipes.

## Step 4: Test the System

### Option A: Test PDF Processing

```bash
python test_pdf_upload.py
```

This will test:

- PDF text extraction
- Recipe parsing
- Vector store connection
- Search functionality

### Option B: Upload Recipes to Pinecone

```bash
python upload_recipes_from_pdf.py --pdf-dir pdf_recipes
```

This will:

- Process all PDF files in the `pdf_recipes` directory
- Extract recipes using AI
- Upload them to Pinecone with embeddings
- Provide detailed logging

## Step 5: Verify Upload (recipe endpoints removed)

### Check via API

Start the FastAPI server:

```bash
python main.py
```

Recipe-related API endpoints have been removed from the server.

### Check via Python

Vector store examples have been removed.

## Step 6: Upload Your Own PDF Recipes

1. **Prepare your PDF files**:

   - Ensure they contain readable text (not just images)
   - Each recipe should have clear sections for ingredients and instructions
   - Place them in the `pdf_recipes` directory

2. **Upload via command line**:

```bash
python upload_recipes_from_pdf.py --pdf-dir pdf_recipes
```

3. **Upload via API**: Removed.

## PDF Format Requirements

For best results, your PDF recipes should include:

- **Recipe name** (clear title)
- **Ingredients list** (with quantities)
- **Cooking instructions** (step-by-step)
- **Optional**: Cuisine type, difficulty, cooking time, servings

### Example PDF Structure:

```
Spaghetti Carbonara

Ingredients:
• 400g spaghetti
• 200g guanciale, diced
• 4 large eggs
• 100g Pecorino Romano cheese

Instructions:
1. Bring a large pot of salted water to boil
2. Cook spaghetti according to package directions
3. Heat skillet and cook guanciale until crispy
4. Mix eggs and cheese in a bowl
5. Combine pasta with guanciale and egg mixture
```

## Troubleshooting

### Common Issues:

1. **"No PDF files found"**

   - Ensure PDF files are in the `pdf_recipes` directory
   - Check file extensions are `.pdf` (lowercase)

2. **"Error extracting text from PDF"**

   - PDF might be image-based (scanned)
   - Try converting to text-based PDF first
   - Ensure PDF is not password-protected

3. **"No recipes found in PDF"**

   - Check PDF contains readable text
   - Ensure recipe structure is clear
   - Try with the sample PDF first

4. **"Pinecone connection error"**

   - Verify PINECONE_API_KEY is correct
   - Check internet connection
   - Ensure Pinecone index exists

5. **"OpenAI API error"**
   - Verify OPENAI_API_KEY is correct
   - Check API key has sufficient credits
   - Ensure API key has access to GPT-4o

### Debug Mode:

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Advanced Usage

### Custom PDF Processing

PDF processing has been removed from CVP Lite.

### Custom Vector Store Operations (for internal/testing use)

Vector search examples have been removed.

## API Endpoints

Recipe endpoints have been removed.

## Next Steps

After successfully uploading recipes:

1. **Test search functionality** with various queries
2. **Integrate with your application** using the API endpoints
3. **Scale up** by processing larger recipe collections
4. **Customize** the recipe parsing logic for your specific needs

## Support

If you encounter issues:

1. Check the logs for detailed error messages
2. Verify all API keys are correct
3. Test with the sample PDF first
4. Ensure your PDF files contain readable text

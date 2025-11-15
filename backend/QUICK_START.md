# Quick Start Guide - Fairly Backend API

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Create Database Indexes

```bash
python api/create_indexes.py
```

**Alternative (if you get import errors):**
```bash
python -m api.create_indexes
```

### Step 3: Start the Server

```bash
python run_api.py
```

That's it! Your API is now running at `http://localhost:8000`

## 📚 Next Steps

1. **View API Documentation**: Open http://localhost:8000/docs in your browser
2. **Test the API**: Use the Swagger UI to test endpoints interactively
3. **Connect Frontend**: Update frontend `.env.local` with:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_USE_MOCK_API=false
   ```

## ✅ Verification

Test the health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

## 🎯 Key Features

- **9 RESTful Endpoints**: Complete CRUD for chats and messages
- **AI Integration**: Automatic AI responses using your RAG system
- **MongoDB Storage**: Persistent data storage
- **Auto Documentation**: Swagger UI at `/docs`
- **CORS Enabled**: Ready for frontend integration

## 🐛 Troubleshooting

**Port already in use?**
- Change `API_PORT` in `.env` or kill the process using port 8000

**MongoDB connection failed?**
- Verify credentials in `.env`
- Check MongoDB Atlas IP whitelist

**Search engine not working?**
- Verify Gemini and Pinecone API keys in `.env`
- Check that Pinecone index exists

## 📖 Full Documentation

See `README.md` for complete documentation.


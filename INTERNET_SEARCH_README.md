# Internet Search Feature for RAG Chatbot

This document describes the internet search functionality that has been added to the RAG Chatbot system, allowing sessions to search the internet for current information when needed.

## Overview

The internet search feature integrates DuckDuckGo search capabilities into the RAG system, enabling the chatbot to provide up-to-date information by searching the web when appropriate. This feature is session-based and can be enabled/disabled per session by administrators.

## Features

### 🔍 **Smart Search Detection**
- Automatically detects when a query would benefit from internet search
- Uses keyword analysis and pattern matching to identify current information needs
- Examples of queries that trigger search:
  - "What's the latest news about AI?"
  - "Current weather in New York"
  - "Latest stock prices for Apple"
  - "Breaking news today"

### 🌐 **DuckDuckGo Integration**
- Uses DuckDuckGo's instant answer API for quick responses
- Falls back to web search for comprehensive results
- No API key required (uses public DuckDuckGo search)
- Respects rate limits and provides reliable results

### 🧠 **Intelligent Response Combination**
- Combines internet search results with document context
- Prioritizes current information while maintaining document relevance
- Handles conflicts between sources gracefully
- Provides source attribution for transparency

### ⚙️ **Session-Based Control**
- Internet search can be enabled/disabled per session
- Administrators can control which sessions have internet access
- Toggle can be changed at any time without affecting existing data

## Technical Implementation

### Backend Components

#### 1. Database Schema Updates
```sql
-- Added to chat_sessions table
ALTER TABLE chat_sessions ADD COLUMN enable_internet_search BOOLEAN DEFAULT FALSE;
```

#### 2. Search Service (`backend/search_service.py`)
- `DuckDuckGoSearchService` class handles all search operations
- Methods:
  - `search()`: Main search function combining instant answers and web results
  - `search_instant_answer()`: Gets quick answers from DuckDuckGo
  - `search_web()`: Performs comprehensive web search
  - `is_search_needed()`: Determines if a query needs internet search
  - `format_search_results_for_llm()`: Formats results for LLM consumption

#### 3. RAG Service Integration (`backend/rag_service.py`)
- Enhanced `chat_with_memory()` method includes internet search
- Search is performed after MCP tools but before document-based RAG
- Results are combined intelligently with document context

#### 4. API Updates
- Updated schemas to include `enable_internet_search` field
- Admin endpoints support toggling internet search per session
- Session creation includes internet search option

### Frontend Components

#### 1. Admin Dashboard Updates
- New "Internet Search" column in sessions table
- Toggle button to enable/disable search per session
- Checkbox in session creation modal
- Visual indicators showing search status

#### 2. Type Definitions
- Updated `ChatSession` interface to include `enable_internet_search`
- Updated `ChatSessionCreate` interface for session creation

## Usage

### For Administrators

1. **Enable Internet Search for a Session:**
   - Go to Admin Dashboard
   - Find the session in the sessions table
   - Click "Enable Search" button in the Actions column
   - The status will change to "Enabled" in the Internet Search column

2. **Create New Session with Internet Search:**
   - Click "Create Session" button
   - Fill in session details
   - Check "Enable Internet Search" checkbox
   - Click "Create Session"

3. **Disable Internet Search:**
   - Click "Disable Search" button for the session
   - Status will change to "Disabled"

### For Users

1. **Using Sessions with Internet Search:**
   - Internet search is automatic when enabled
   - Ask questions that need current information
   - The system will automatically search the internet when appropriate
   - Responses will include both document context and current information

2. **Example Queries:**
   - "What are the latest developments in machine learning?"
   - "Current market trends in renewable energy"
   - "Recent news about climate change"
   - "Today's weather forecast"

## Configuration

### Environment Variables
No additional environment variables are required. The search service uses DuckDuckGo's public API.

### Dependencies
The following packages are required (already included in requirements.txt):
```
beautifulsoup4==4.12.2
requests==2.31.0
```

## Search Behavior

### When Search is Triggered
The system automatically searches the internet when:
- Query contains current information keywords (latest, recent, today, now, etc.)
- Query asks about news, updates, or time-sensitive information
- Query mentions specific years (2024, 2025, etc.)
- Query patterns suggest need for current data

### When Search is NOT Triggered
The system will NOT search the internet for:
- General knowledge questions
- Historical information
- Questions about uploaded documents
- Queries that don't suggest need for current information

### Response Format
When internet search is used, responses include:
- Information from uploaded documents (if relevant)
- Current information from internet search
- Source attribution
- Conflict resolution when sources disagree

## Testing

### Test Script
Run the test script to verify functionality:
```bash
python test_internet_search.py
```

This script tests:
- Search service functionality
- Search need detection
- RAG integration
- Dependencies

### Manual Testing
1. Create a session with internet search enabled
2. Ask questions like:
   - "What's the latest news about AI?"
   - "Current weather in your city"
   - "Latest developments in renewable energy"
3. Verify responses include current information
4. Check that document-based questions still work normally

## Troubleshooting

### Common Issues

1. **Search Not Working:**
   - Check if internet search is enabled for the session
   - Verify internet connectivity
   - Check if query actually needs internet search

2. **No Search Results:**
   - DuckDuckGo may be temporarily unavailable
   - Query might not match search patterns
   - Check network connectivity

3. **Slow Responses:**
   - Internet search adds latency
   - Consider disabling for sessions that don't need it
   - Check network speed

### Debug Information
The system logs search activities:
- Search queries and results
- Search need detection decisions
- Integration with RAG responses

## Security Considerations

### Privacy
- DuckDuckGo is used for privacy-focused search
- No user data is sent to external services beyond search queries
- Search queries are not stored permanently

### Rate Limiting
- Built-in delays prevent overwhelming DuckDuckGo
- Respects DuckDuckGo's terms of service
- Graceful fallback when search fails

### Content Filtering
- Results are processed by the LLM for appropriateness
- No direct display of unfiltered search results
- Source attribution helps users verify information

## Future Enhancements

### Potential Improvements
1. **Search Result Caching:** Cache results to reduce API calls
2. **Custom Search Providers:** Support for other search engines
3. **Search Result Filtering:** More sophisticated content filtering
4. **Search Analytics:** Track search usage and effectiveness
5. **Custom Search Patterns:** Allow custom search trigger patterns

### Configuration Options
1. **Search Provider Selection:** Choose between different search engines
2. **Result Limit Configuration:** Adjust number of search results
3. **Search Timeout Settings:** Configure search timeouts
4. **Custom Keywords:** Add custom search trigger keywords

## Support

For issues or questions about the internet search feature:
1. Check the troubleshooting section above
2. Run the test script to verify functionality
3. Check the logs for error messages
4. Ensure all dependencies are installed correctly

The internet search feature enhances the RAG chatbot's capabilities by providing access to current information while maintaining the privacy and reliability of the document-based knowledge system.

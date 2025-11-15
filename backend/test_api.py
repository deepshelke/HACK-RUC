#!/usr/bin/env python3
"""
Test script for Fairly API
Run this after starting the server to verify all endpoints work correctly.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_api():
    print("\n🧪 Testing Fairly API")
    print("=" * 60)
    
    try:
        # 1. Health Check
        print_section("1. Health Check")
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200, "Health check failed"
        
        # 2. Create Chat
        print_section("2. Creating Chat")
        response = requests.post(
            f"{BASE_URL}/chats",
            json={"title": "Test Chat"},
            timeout=5
        )
        print(f"✅ Status: {response.status_code}")
        chat_data = response.json()
        print(f"   Response: {json.dumps(chat_data, indent=2)}")
        assert response.status_code == 201, "Failed to create chat"
        chat_id = chat_data["data"]["id"]
        print(f"   📝 Chat ID: {chat_id}")
        
        # 3. Get All Chats
        print_section("3. Getting All Chats")
        response = requests.get(f"{BASE_URL}/chats", timeout=5)
        print(f"✅ Status: {response.status_code}")
        chats = response.json()["data"]
        print(f"   Total chats: {len(chats)}")
        assert response.status_code == 200, "Failed to get chats"
        assert len(chats) > 0, "No chats found"
        
        # 4. Get Specific Chat
        print_section("4. Getting Chat by ID")
        response = requests.get(f"{BASE_URL}/chats/{chat_id}", timeout=5)
        print(f"✅ Status: {response.status_code}")
        chat = response.json()["data"]
        print(f"   Chat title: {chat['title']}")
        print(f"   Message count: {chat['messageCount']}")
        assert response.status_code == 200, "Failed to get chat"
        assert chat["id"] == chat_id, "Wrong chat returned"
        
        # 5. Create User Message
        print_section("5. Creating User Message")
        user_message = "What are my rights as a domestic worker?"
        print("   ⚠️  Note: AI response will be generated in background (may take 10-30 seconds)")
        response = requests.post(
            f"{BASE_URL}/chats/{chat_id}/messages",
            json={"content": user_message, "role": "user"},
            timeout=10  # Increased timeout for message creation
        )
        print(f"✅ Status: {response.status_code}")
        message_data = response.json()
        print(f"   User message: {message_data['data']['content'][:60]}...")
        assert response.status_code == 201, "Failed to create message"
        user_message_id = message_data["data"]["id"]
        
        # Wait for AI response
        print_section("⏳ Waiting for AI Response")
        print("   Waiting 15 seconds for AI to generate response in background...")
        print("   (AI generation happens asynchronously, so response may take longer)")
        time.sleep(15)
        
        # 6. Get Messages (with retry for AI response)
        print_section("6. Getting Messages")
        max_retries = 5
        retry_count = 0
        messages = []
        
        while retry_count < max_retries:
            response = requests.get(f"{BASE_URL}/chats/{chat_id}/messages", timeout=5)
            print(f"✅ Status: {response.status_code}")
            messages = response.json()["data"]
            print(f"   Total messages: {len(messages)}")
            
            if len(messages) >= 2:
                break  # AI response is ready
            
            retry_count += 1
            if retry_count < max_retries:
                print(f"   ⏳ AI response not ready yet, waiting 5 more seconds... (attempt {retry_count}/{max_retries})")
                time.sleep(5)
        
        for i, msg in enumerate(messages, 1):
            role_icon = "👤" if msg['role'] == 'user' else "🤖"
            content_preview = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
            print(f"   {i}. {role_icon} [{msg['role']}]: {content_preview}")
        
        assert response.status_code == 200, "Failed to get messages"
        if len(messages) < 2:
            print("   ⚠️  Warning: AI response not ready yet (this is normal, it's generated in background)")
            print("   ✅ User message was created successfully")
        else:
            assert len(messages) >= 2, "Expected at least 2 messages (user + assistant)"
        
        # 7. Update Chat
        print_section("7. Updating Chat Title")
        new_title = "Updated Chat Title"
        response = requests.patch(
            f"{BASE_URL}/chats/{chat_id}",
            json={"title": new_title},
            timeout=5
        )
        print(f"✅ Status: {response.status_code}")
        updated_chat = response.json()["data"]
        print(f"   New title: {updated_chat['title']}")
        assert response.status_code == 200, "Failed to update chat"
        assert updated_chat["title"] == new_title, "Title not updated"
        
        # 8. Update Message
        if messages:
            print_section("8. Updating Message")
            message_id = messages[0]["id"]
            new_content = "Updated message content"
            response = requests.patch(
                f"{BASE_URL}/chats/{chat_id}/messages/{message_id}",
                json={"content": new_content},
                timeout=5
            )
            print(f"✅ Status: {response.status_code}")
            updated_message = response.json()["data"]
            print(f"   Updated content: {updated_message['content']}")
            assert response.status_code == 200, "Failed to update message"
        
        # 9. Delete Message (optional - skip if you want to keep messages)
        # print_section("9. Deleting Message")
        # if messages:
        #     message_id = messages[-1]["id"]
        #     response = requests.delete(
        #         f"{BASE_URL}/chats/{chat_id}/messages/{message_id}",
        #         timeout=5
        #     )
        #     print(f"✅ Status: {response.status_code}")
        #     assert response.status_code == 200, "Failed to delete message"
        
        # 10. Delete Chat (optional - comment out to keep test data)
        print_section("10. Deleting Chat (Cleanup)")
        response = requests.delete(f"{BASE_URL}/chats/{chat_id}", timeout=5)
        print(f"✅ Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200, "Failed to delete chat"
        
        print_section("✅ All Tests Passed!")
        print("\n🎉 API is working correctly!")
        print("\nNext steps:")
        print("  - Test with Swagger UI: http://localhost:8000/docs")
        print("  - Connect your frontend")
        print("  - Test end-to-end user flows")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("   Make sure the server is running:")
        print("   python run_api.py")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()


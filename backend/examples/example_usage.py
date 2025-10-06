"""
Example usage of the Job Copilot API

This demonstrates the complete workflow:
1. Create a user
2. Create a user profile with embeddings
3. Search for compatible jobs
4. Create an application
5. Get AI insights
"""

import asyncio
import httpx
from uuid import UUID

BASE_URL = "http://localhost:8000/api/v1"


async def main():
    async with httpx.AsyncClient() as client:
        
        # 1. Create a user
        print("📝 Creating user...")
        user_response = await client.post(
            f"{BASE_URL}/users/",
            json={
                "email": "john.doe@example.com",
                "full_name": "John Doe"
            }
        )
        user_data = user_response.json()
        user_id = user_data["id"]
        print(f"✅ User created: {user_id}")
        
        # 2. Create user profile
        print("\n👤 Creating user profile...")
        profile_response = await client.post(
            f"{BASE_URL}/users/{user_id}/profile",
            json={
                "resume_text": "Experienced software engineer with 5 years in Python and AI...",
                "skills": [
                    "Python", "FastAPI", "PostgreSQL", "Machine Learning",
                    "LangChain", "Docker", "AWS"
                ],
                "experience": {
                    "total_years": 5,
                    "positions": [
                        {
                            "title": "Senior Software Engineer",
                            "company": "Tech Corp",
                            "duration": "3 years",
                            "achievements": [
                                "Built scalable API serving 1M+ requests/day",
                                "Led team of 4 engineers"
                            ]
                        }
                    ]
                },
                "education": {
                    "degree": "BS Computer Science",
                    "university": "State University"
                },
                "career_goals": "Looking to work on cutting-edge AI applications in a fast-paced startup environment",
                "preferences": {
                    "salary_min": 120000,
                    "salary_max": 180000,
                    "remote": True,
                    "locations": ["San Francisco", "Remote"]
                }
            }
        )
        print(f"✅ Profile created with embeddings")
        
        # 3. Search for compatible jobs
        print("\n🔍 Searching for compatible jobs...")
        jobs_response = await client.get(
            f"{BASE_URL}/jobs/search",
            params={
                "user_id": user_id,
                "limit": 5,
                "min_score": 0.7
            }
        )
        jobs_data = jobs_response.json()
        print(f"✅ Found {jobs_data['total']} compatible jobs")
        
        if jobs_data['jobs']:
            top_job = jobs_data['jobs'][0]
            print(f"\n🎯 Top match:")
            print(f"   Title: {top_job['title']}")
            print(f"   Company: {top_job['company']}")
            print(f"   Compatibility: {top_job['compatibility_score']:.2%}")
            print(f"   Skills match: {top_job['breakdown']['skills_match']:.2%}")
            print(f"   Experience match: {top_job['breakdown']['experience_match']:.2%}")
            
            job_id = top_job['id']
            
            # 4. Create application
            print("\n📄 Creating application...")
            app_response = await client.post(
                f"{BASE_URL}/applications/",
                json={
                    "user_id": user_id,
                    "job_id": job_id
                }
            )
            app_data = app_response.json()
            application_id = app_data['id']
            print(f"✅ Application created: {application_id}")
            
            # 5. Get compatibility details
            print("\n🤖 Getting AI insights...")
            insights_response = await client.get(
                f"{BASE_URL}/intelligence/compatibility/{user_id}/{job_id}"
            )
            insights = insights_response.json()
            print(f"✅ Compatibility analysis:")
            print(f"   Overall: {insights['compatibility']['overall_score']:.2%}")
            print(f"   Skills: {insights['compatibility']['skills_match']:.2%}")
            print(f"   Experience: {insights['compatibility']['experience_match']:.2%}")
            print(f"   Goals alignment: {insights['compatibility']['goals_alignment']:.2%}")
            
            # 6. Get recommendations
            print("\n💡 Getting job recommendations...")
            rec_response = await client.get(
                f"{BASE_URL}/intelligence/recommendations/{user_id}"
            )
            recommendations = rec_response.json()
            print(f"✅ Top recommendations:")
            for i, rec in enumerate(recommendations['recommendations'][:3], 1):
                print(f"   {i}. {rec['title']} at {rec['company']}")
                print(f"      Score: {rec['score']:.2%}")
                print(f"      Reason: {rec['reason']}")


if __name__ == "__main__":
    print("🚀 Job Copilot API Example\n")
    asyncio.run(main())
    print("\n✨ Complete!")

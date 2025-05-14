import json
import time
import os
import requests

locations = [
    "Russia", "India", "Pakistan", "China", "Brazil", "Mexico", "Argentina", 
    "Chile", "Colombia", "Venezuela", "Peru", "Ecuador", "Bolivia", "Paraguay", 
    "Uruguay", "Costa Rica", "Honduras", "Nicaragua", "El Salvador", "Guatemala", 
    "Haiti", "Dominican Republic", "Puerto Rico", "Cuba", "Jamaica", 
    "Trinidad and Tobago", "Bahamas", "Barbados", "Belize", "Grenada", 
    "Guyana", "Suriname", "Trinidad and Tobago", "Bahamas", "Barbados", 
    "Belize", "Grenada", "Guyana", "Suriname"
]

class GitHubEmailFinder:
    """
    A class to find GitHub users by location and skills, and extract their email addresses.
    """
    def __init__(self, token, location, skills=None):
        self.token = token
        self.location = location
        self.skills = skills if skills else []
        self.api_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def search_users_by_location_and_skills(self):
        """
        Search for GitHub users by location and skills.
        """
        users = []
        page = 1
        
        # Build the query string similar to the GitHub web interface
        skill_query = " OR ".join([f'"{skill}"' for skill in self.skills])
        # query_string = f"type:user+location:{self.location}+{skill_query}&s=followers&o=desc"
        query_string = f"created%3A<2017-01-01+location:{self.location}+developer&type=users&ref=advsearch"
        
        
        print("--------------------------------")
        print(f"Query string: {query_string}")
        print("--------------------------------")
        
        while True:
            search_url = f"{self.api_url}/search/users?q={query_string}&page={page}&per_page=100"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                print(f"Failed to fetch users: {response.json()}")
                break

            data = response.json()
            users.extend(data['items'])
            
            # Check if there are more pages
            if len(data['items']) < 100:
                break
                
            page += 1
            time.sleep(2)  # To respect API rate limit

        return users

    def get_email_from_user(self, username):
        """
        Retrieve the email address of a GitHub user by their username.
        """
        user_url = f"{self.api_url}/users/{username}"
        response = requests.get(user_url, headers=self.headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            email = user_data.get('email')
            if email:
                return email

            # If email is not in profile, check public events
            events_url = f"{self.api_url}/users/{username}/events/public"
            events_response = requests.get(events_url, headers=self.headers, timeout=10)
            if events_response.status_code == 200:
                events_data = events_response.json()
                for event in events_data:
                    commits = event.get('payload', {}).get('commits', [])
                    for commit in commits:
                        author = commit.get('author', {})
                        email = author.get('email')
                        if email:
                            return email
        return None

    def get_user_repos(self, username):
        """
        Get the repositories of a GitHub user by their username.
        """
        repos_url = f"{self.api_url}/users/{username}/repos"
        response = requests.get(repos_url, headers=self.headers, timeout=10)
        if response.status_code == 200:
            repos_data = response.json()
            return repos_data
        return None

    def find_users_with_skills(self, users, skills):
        """
        Find users with specific skills from a list of users.
        """
        skilled_users = []
        for user in users:
            repos = self.get_user_repos(user['login'])
            if repos:
                for repo in repos:
                    # Safely handle the description field
                    description = repo.get('description', '')
                    if description:  # Check if description is not None
                        description = description.lower()
                    topics = repo.get('topics', [])
                    if any(skill.lower() in description for skill in skills) or any(skill.lower() in topics for skill in skills):
                        skilled_users.append(user)
                        break
        return skilled_users

    def find_emails(self):
        """
        Find and return non-Gmail email addresses of users.
        """
        # Use the new search method that combines location and skills
        users = self.search_users_by_location_and_skills()
        
        print("--------------------------------")
        print(f"Searching for users in {self.location} with skills: {self.skills}")
        print("--------------------------------")
        print(f"Found {len(users)} users")
        print("--------------------------------")
        
        non_gmail_emails = []

        for user in users:
            email = self.get_email_from_user(user['login'])
            if email and not email.endswith("@users.noreply.github.com"):
                non_gmail_emails.append(email)
                print(f"{email}")
            time.sleep(1)  # To respect API rate limit

        return non_gmail_emails


def main():
    token = ""  # Replace with your GitHub token
    
    for location in locations:
    
        skills = ["AI", "ML", "Machine Learning", "MLOps", "LLMs", "Artificial Intelligence"]  # Specify the skills
        
        skills_script = " _ ".join([f'{skill}' for skill in skills])
        
        finder = GitHubEmailFinder(token, location, skills)
        emails = finder.find_emails()

        # Create the new directory if it doesn't exist
        new_dir = "new"
        os.makedirs(new_dir, exist_ok=True)

        # Save non-Gmail emails to a file
        with open(f"{new_dir}/{location}_{skills_script}_emails.json", "w", encoding="utf-8") as f:
            json.dump(emails, f, indent=4)


if __name__ == "__main__":
    main()

from safety_review import flag_post

def main():
    posts = [
        "Wow I love this new app!",
        "Feeling sad… thinking about suicide",
        "Check out my vacation pics!"
    ]

    for i, p in enumerate(posts, 1):
        result = flag_post(p)
        print(f"Post {i}: {p}")
        print("  →", result)

if __name__ == "__main__":
    main()

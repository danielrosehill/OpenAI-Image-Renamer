import os
import base64
import re
from pathlib import Path
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# File extensions considered valid images
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def describe_image(path: Path) -> str:
    with open(path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that generates short, descriptive filenames "
                    "for image files. Use lowercase words separated by hyphens. Do not include articles, "
                    "punctuation, or unnecessary adjectives. Describe the main subject briefly. "
                    "Avoid generic terms like 'collage', 'variety', or 'image'."
                )
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Generate a short filename for this image:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }
        ],
        max_tokens=50,
    )
    return response.choices[0].message.content.strip()

def normalize_filename(description, existing_names, ext):
    base = re.sub(r'[^a-z0-9]+', '-', description.lower()).strip('-')
    name = base
    counter = 1
    while (name + ext) in existing_names:
        name = f"{base}-{counter}"
        counter += 1
    existing_names.add(name + ext)
    return name + ext

def rename_images_recursively(root_dir: Path):
    existing_names = set()
    print(f"\n🔍 Scanning: {root_dir}")
    for file_path in sorted(root_dir.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            try:
                desc = describe_image(file_path)
                new_name = normalize_filename(desc, existing_names, file_path.suffix.lower())
                new_path = file_path.with_name(new_name)
                file_path.rename(new_path)
                print(f"✔ {file_path.relative_to(root_dir)} → {new_name}")
            except Exception as e:
                print(f"✘ Failed {file_path.relative_to(root_dir)}: {e}")

def main():
    folder_input = input("Enter the top-level image folder path: ").strip()
    root_dir = Path(folder_input).expanduser().resolve()

    if not root_dir.is_dir():
        print(f"Error: '{root_dir}' is not a valid directory.")
        return

    rename_images_recursively(root_dir)

if __name__ == "__main__":
    main()

import os

from users.models import User


def notion_to_text_file():
    file_path = os.path.join(os.path.dirname(__file__), "notion.txt")
    with open(file_path, "w") as f:
        user = User.objects.get(email="ddr04014@gmail.com")
        for item in user.originaldocument_set.all():
            if item.text:
                f.write(f"# {item.title}\n{item.text}\n")

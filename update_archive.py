from pathlib import Path
from bs4 import BeautifulSoup
import shutil
from datetime import datetime

# Copy past week to archive
date = datetime.now()
from_file = Path("docs/index.html")
to_file = Path(f"docs/archive/{date.strftime('%Y-%m-%d')}.html")
shutil.copy(from_file, to_file)

# Update archive
soup = BeautifulSoup(Path("docs/archive/index.html").read_text(), 'html.parser')
link = soup.new_tag("a", href=f"{date.strftime('%Y-%m-%d')}.html")
link.string = date.strftime("%d %b %Y")
list_item = soup.new_tag("li")
list_item.append(link)
soup.find("ul", id="dates").insert(0, list_item)
Path("docs/archive/index.html").write_text(soup.prettify())

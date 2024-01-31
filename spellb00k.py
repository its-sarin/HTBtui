from textual import on
from textual.app import App
from textual.widgets import RichLog

from rich.markdown import Markdown

from screens.htb_screen import HTBScreen


# markdown test
MARKDOWN = """
# This is an h1

Rich can do a pretty *decent* job of rendering markdown.

1. This is a list item
2. This is another list item
"""

class spellb00k(App):
        
    SCREENS = {"htb_screen": HTBScreen()}
    
    def on_ready(self) -> None:
        """
        Event handler for when the application is ready.
        """
        log = self.query_one(RichLog)
        log.write("[bold purple]Welcome to spellb00k!")

        # testing markdown support
        md = Markdown(MARKDOWN)
        log.write(md)

    async def on_mount(self) -> None:
        """
        Event handler for when the application is mounted.
        """
        self.push_screen("htb_screen")
        

if __name__ == "__main__":
    app = spellb00k()
    app.run()
    
    
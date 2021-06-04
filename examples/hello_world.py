# Hello World!
# A simple example to get you started with Wave.
# #hello_world
# ---
from wavegui import ui, app, Q


@app('/demo')
async def demo(q: Q):
    # Add a Markdown card named `hello` to the page.
    q.page['hello'] = ui.markdown_card(
        box='1 1 2 2',
        title='Hello World!',
        content='And now for something completely different!',
    )

    # Finally, sync the page to send our changes to the server.
    await q.page.save()

if __name__ == '__main__':
    app.run()
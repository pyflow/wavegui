# Hello World!
# A simple example to get you started with Wave.
# #hello_world
# ---
import asyncio
from wavegui import ui, app, Q

async def counter_back(q:Q):
    for count in range(1, 101):
        q.page['counter'] = ui.markdown_card(
            box='1 1 2 2',
            title=f'Counter: {count}',
            content='The count number will increase automatically!',
        )

        # Finally, sync the page to send our changes to the server.
        await q.page.save()
        print(f'save page {count}')
        await asyncio.sleep(1)

@app('/counter')
async def counter(q: Q):
    # Add a Markdown card named `hello` to the page
    print(q.url)
    print(q.headers)
    q.page['counter'] = ui.markdown_card(
            box='1 1 2 2',
            title='Counter: 0',
            content='The counter not started!',
        )
    await q.page.save()
    print('init page saved.')

    await q.run_in_back(counter_back(q))
    print('counter return.')


if __name__ == '__main__':
    app.run()
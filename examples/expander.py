
from wavegui import ui, app, Q


@app('/expander')
async def expander(q: Q):
    q.page['form'] = ui.form_card(
        box='1 1 4 8',
        items=[ui.expander(name='expander', label='Expander example', items=[
            ui.textbox(name='textbox1', label='Textbox 1'),
            ui.textbox(name='textbox2', label='Textbox 2'),
            ui.textbox(name='textbox3', label='Textbox 3'),
            ui.expander(name='expander_2', label='Sub Expander example', items=[
                ui.textbox(name='textbox1', label='Textbox 1'),
                ui.textbox(name='textbox2', label='Textbox 2'),
                ui.textbox(name='textbox3', label='Textbox 3'),
            ])
        ])],
    )

    # Finally, sync the page to send our changes to the server.
    await q.page.save()

if __name__ == '__main__':
    app.run()
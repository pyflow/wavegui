import os
import os.path
from wavegui import ui, app, Q


def make_link_list(links):
    # Make a markdown list of links.
    return '\n'.join([f'- [{os.path.basename(link)}]({link})' for link in links])


@app('/upload')
async def upload(q: Q):
    print('upload', q)
    if q.args.user_files:
        q.page['example'].items = [
            ui.text_xl('Files uploaded!'),
            ui.text(make_link_list(q.args.user_files)),
            ui.button(name='back', label='Back', primary=True),
        ]
    else:
        q.page['example'] = ui.form_card(box='1 1 4 10', items=[
            ui.text_xl('Upload some files'),
            ui.file_upload(name='user_files', label='Upload', multiple=True),
        ])
    await q.page.save()

if __name__ == '__main__':
    app.run()

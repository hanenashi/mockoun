from flask import Flask, request, redirect, make_response
import time

app = Flask(__name__)

# In-memory database to hold the messages you send from the new GUI
NEW_POSTS = []
POST_ID_COUNTER = 60000 

@app.route('/myBoards.jsp', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('login', 'blaznik')
        resp = make_response(redirect('/myBoards.jsp'))
        resp.set_cookie('okoun_session', username)
        return resp
    
    session_user = request.cookies.get('okoun_session')
    if session_user:
        return f'<!DOCTYPE html><html><body><div class="user">Přihlášen jako: <b>{session_user}</b></div></body></html>'
    else:
        return '<!DOCTYPE html><html><body><form class="login" method="POST" action="/myBoards.jsp"><input name="login" type="text" /><input name="password" type="password" /><button class="submit" type="submit">Log in</button></form></body></html>'

@app.route('/boards/<club_id>', methods=['GET', 'POST'])
def club(club_id):
    global POST_ID_COUNTER
    session_user = request.cookies.get('okoun_session', 'Anon')

    # ---> NEW: Handle incoming posts from the Harvester <---
    if request.method == 'POST':
        text = request.form.get('body', '')
        if text:
            NEW_POSTS.insert(0, {
                "id": POST_ID_COUNTER,
                "user": session_user,
                "html": text
            })
            POST_ID_COUNTER += 1
        # Redirect back to the GET route to see the new post
        return redirect(f'/boards/{club_id}')

    page = int(request.args.get('page', 1))
    posts_html = ""
    
    # Render the user-submitted posts first
    if page == 1:
        for post in NEW_POSTS:
            posts_html += f'''
            <div class="item" id="article-{post['id']}">
                <span class="user">{post['user']}</span>
                <div class="content">{post['html']}</div>
            </div>
            '''

    # Render the generated mock posts
    start_id = 50000 - (page * 10)
    for i in range(5):
        post_id = start_id - i
        posts_html += f'''
        <div class="item" id="article-{post_id}">
            <span class="user">mock_uživatel_{post_id % 3}</span>
            <div class="content">Zkušební zpráva #{post_id} v klubu {club_id}.</div>
        </div>
        '''
        
    older_link = f'<a class="older" href="?page={page+1}">Starší</a>' if page < 3 else ""

    # ---> NEW: Add the legacy posting form at the bottom <---
    form_html = f'''
    <form class="post-form" method="POST" action="/boards/{club_id}">
        <textarea name="body" rows="4" cols="50"></textarea>
        <button type="submit" class="submit-post">Odeslat</button>
    </form>
    '''

    return f"<!DOCTYPE html><html><body><h1>Klub: {club_id}</h1><div class='board'>{posts_html}</div>{older_link}<hr>{form_html}</body></html>"

if __name__ == '__main__':
    app.run(port=5000, debug=True)
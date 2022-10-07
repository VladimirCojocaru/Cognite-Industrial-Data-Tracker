fetch('http://localhost:9090/session')
    .then((response) => {
        if (response.status == 511) {
            document.getElementById('login').innerHTML = '<a class="login-btn" href="http://localhost:9090/backend">Log in</a>';
            document.getElementById('explore_assets').innerHTML = '<a href="http://localhost:9090/backend" class="explore_assets_button">Explore available assets</a>';
        } else
        if (response.status == 200) {
            document.getElementById('login').innerHTML = '<a class="login-btn" href="http://localhost:9090/logout">Log out</a>';
            document.getElementById('explore_assets').innerHTML = '<a href="assets.html" class="explore_assets_button">Explore available assets</a>';
        }
    })
    .catch((err) => {
        console.log(err)
    })
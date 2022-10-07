const template = document.createElement('template');

template.innerHTML = `
<div class="navigation_bar">
    <nav>
        <ul>
            <li><a class="home-btn" href="index.html">Home</a></li>
            <li><a class="logo"        href="index.html">Cognite Industrial<span> Data</span></a></li>
            <li id="login"></li>
        </ul>
    </nav>
</div>
`;

document.body.appendChild(template.content);
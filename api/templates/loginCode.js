const loginBox = document.querySelector("#login-content");
const form = document.querySelector("#login-content form");
const usernameBox = document.querySelector("#username");
const passwordBox = document.querySelector("#password");
const messageBox = document.querySelector("#message");

function loginSuccess(data) {
    const success = data.{{ consts.FIELD_SUCCESS }};
    if (success) {
        messageBox.textContent = "Eingeloggt.";
        location.reload();
    }
    else {
        switch (data.{{ consts.FIELD_REASON }}) {
            case "{{ exceptions.NotFoundError.identifier }}":
                messageBox.textContent = "Nutzername nicht gefunden.";
                break;
            case "{{ exceptions.InvalidCredentials.identifier }}":
                messageBox.textContent = "Falsche Einlogdaten.";
                break;
            default:
                messageBox.textContent = "Konnte nicht eingeloggt werden.";
        }
    }
    messageBox.style.visibility = "visible";
}
form.addEventListener("submit", (event) => {
    event.preventDefault();
    fetch("{{ url_for('login') }}", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "POST",
        body: JSON.stringify({ {{ consts.FIELD_USERNAME }}: usernameBox.value, {{ consts.FIELD_PASSWORD }}: passwordBox.value })
    }).then((response) => response.json()).then(loginSuccess);
}, true);
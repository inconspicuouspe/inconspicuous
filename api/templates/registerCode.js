const loginBox = document.querySelector("#signup-content");
const form = document.querySelector("#signup-content form");
const usernameBox = document.querySelector("#username");
const passwordBox = document.querySelector("#password");
const messageBox = document.querySelector("#message");
const userSlot = new URLSearchParams(location.search).get("user_slot");

function signupSuccess(data) {
    const success = data.{{ consts.FIELD_SUCCESS }};
    if (success) {
        messageBox.textContent = "Konto erstellt.";
        location.replace("{{ url_for('home') }}")
    }
    else {
        switch (data.{{ consts.FIELD_REASON }}) {
            case "{{ exceptions.CannotBeNamedAnonymous.identifier }}":
                messageBox.textContent = "Dein Nutzername kann nicht 'Anonymous' sein.";
                break;
            case "{{ exceptions.UsernameInvalidCharacters.identifier }}":
                messageBox.textContent = "Nutzername muss aus den Zeichen a-z, A-Z, 0-9, _ und - bestehen.";
                break;
            case "{{ exceptions.PasswordTooLong.identifier }}":
                messageBox.textContent = "Passwort muss kürzer sein.";
                break;
            case "{{ exceptions.PasswordTooShort.identifier }}":
                messageBox.textContent = "Passwort muss länger sein.";
                break;
            case "{{ exceptions.UsernameTooLong.identifier }}":
                messageBox.textContent = "Nutzername muss kürzer sein.";
                break;
            case "{{ exceptions.UsernameTooShort.identifier }}":
                messageBox.textContent = "Nutzername muss länger sein.";
                break;
            case "{{ exceptions.UserSlotTakenError.identifier }}":
                messageBox.textContent = "Dieser User Slot wird bereits verwendet.";
                break;
            case "{{ exceptions.AlreadyExistsError.identifier }}":
                messageBox.textContent = "Der Nutzername wird bereits verwendet.";
                break;
            case "{{ exceptions.NotFoundError.identifier }}":
                messageBox.textContent = "Du hast keinen angegeben oder dieser User Slot existiert nicht."
                break;
            default:
                messageBox.textContent = "Dein Konto konnte nicht erstellt werden.";
        }
        
    }
    messageBox.style.visibility = "visible";
}
form.addEventListener("submit", (event) => {
    event.preventDefault();
    fetch("{{ url_for('register') }}", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            '{{ consts.FIELD_CSRF_TOKEN_HEADER }}': getCookie("{{ consts.FIELD_CSRF_TOKEN }}")
        },
        method: "POST",
        body: JSON.stringify({ {{ consts.FIELD_USERNAME }}: usernameBox.value, {{ consts.FIELD_PASSWORD }}: passwordBox.value, {{ consts.FIELD_USER_SLOT }}: userSlot })
    }).then((response) => response.json()).then(signupSuccess);
}, true);
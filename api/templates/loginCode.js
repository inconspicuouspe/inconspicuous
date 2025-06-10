const loginBox = document.querySelector("#login-content");
const form = document.querySelector("#login-content form");
const usernameBox = document.querySelector("#username");
const passwordBox = document.querySelector("#password");
const messageBox = document.querySelector("#message");
{# const testButton = document.querySelector(".test-button"); #}
const { startRegistration, startAuthentication } = SimpleWebAuthnBrowser;
async function hashPassword(password, salt = new TextEncoder().encode(btoa("4nd5qW1rb1Q"))) {
    const encoder = new TextEncoder();
    const passwordKey = encoder.encode(password);

    // Import password as a CryptoKey
    const keyMaterial = await crypto.subtle.importKey(
        "raw",
        passwordKey,
        { name: "PBKDF2" },
        false,
        ["deriveBits"]
    );

    // Derive key
    const derivedBits = await crypto.subtle.deriveBits(
        {
            name: "PBKDF2",
            salt: salt,
            iterations: 1_200_000,
            hash: "SHA-256"
        },
        keyMaterial,
        256
    );

    const hashArray = Array.from(new Uint8Array(derivedBits));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

    return hashHex;
}
async function getSecretPasswordData() {
    return encryptWithPublicKey(
        currentPublicKey, btoa(
            await hashPassword(
                JSON.stringify(
                    { username: usernameBox.value, password: passwordBox.value }
                )
            )
        )
    );
}
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
    messageBox.style.display = "block";
}
function sendOldLoginRequest(data) {
    fetch("{{ url_for('old_login') }}", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            '{{ consts.FIELD_CSRF_TOKEN_HEADER }}': getCookie("{{ consts.FIELD_CSRF_TOKEN }}")
        },
        method: "POST",
        body: JSON.stringify({ {{ consts.FIELD_USERNAME }}: usernameBox.value, {{ consts.FIELD_PASSWORD }}: passwordBox.value, {{ consts.FIELD_HASHED_PASSWORD }}: data })
    }).then((response) => response.json()).then(loginSuccess);
}
function sendLoginRequest(data) {
    fetch("{{ url_for('login') }}", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            '{{ consts.FIELD_CSRF_TOKEN_HEADER }}': getCookie("{{ consts.FIELD_CSRF_TOKEN }}")
        },
        method: "POST",
        body: JSON.stringify({ {{ consts.FIELD_USERNAME }}: usernameBox.value, {{ consts.FIELD_PASSWORD }}: data })
    }).then((response) => response.json()).then(loginSuccess);
}
form.addEventListener("submit", (event) => {
    event.preventDefault();
    fetch("{{ url_for('get_login_type') }}", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            '{{ consts.FIELD_CSRF_TOKEN_HEADER }}': getCookie("{{ consts.FIELD_CSRF_TOKEN }}")
        },
        method: "POST",
        body: JSON.stringify({ {{ consts.FIELD_USERNAME }}: usernameBox.value })
    }).then((response) => response.json()).then((json_data) => {
        if (json_data.{{ consts.FIELD_DATA }} === {{ LoginType.WEAK.value }}) {
            getSecretPasswordData().then(sendOldLoginRequest);
        }
        else if (json_data.{{ consts.FIELD_DATA }} === {{ LoginType.SHA3_512_PBKDF2HMAC_100000.value }}) {
            getSecretPasswordData().then(sendLoginRequest);
        }
    })
    
}, true);
{# testButton.addEventListener("click", async (event) => {
    options = JSON.parse(prompt());
    try {
        attResp = await startAuthentication(options);
        console.log(attResp);
    }
    catch (err) {
        alert(err);
    }

}) #}
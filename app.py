from flask import Flask, render_template_string, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        return f"<h2>Thanks {name}! We got your info 🚀</h2><p>Email: {email}</p>"
    
    return render_template_string("""<!doctype html>
<html>
<head>
<title>Lead Site</title>
<style>
body{font-family:Arial;text-align:center;padding:50px;background:#f5f5f5}
form{background:white;padding:30px;border-radius:10px;display:inline-block;box-shadow:0 4px 6px rgba(0,0,0,0.1)}
input,button{padding:10px;margin:5px;width:200px;border:1px solid #ddd;border-radius:5px}
button{background:#2563eb;color:white;border:none;cursor:pointer}
button:hover{background:#1d4ed8}
</style>
</head>
<body>
<h1>Drop Your Details</h1>
<form method="POST">
<input name="name" placeholder="Your Name" required><br>
<input name="email" placeholder="Your Email" type="email" required><br>
<button type="submit">Submit</button>
</form>
</body>
</html>""")

if __name__ == "__main__":
    app.run(debug=True)Enter

from jinja2 import FileSystemLoader, Environment

file_loader = FileSystemLoader('templates')
env = Environment(loader=file_loader)

templates_name = ["glavn", "spisok", "kont"]

SVOwar= [
    {'name': "Создание сайта", 'price': 25000},
    {'name': "Создание нейросети", 'price': 40000},
    {'name': "Парсинг", 'price': 7000}]


for name in templates_name:
    template = env.get_template(f"{name}.html")
    file_name = f"data/{name}.html"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(template.render(SVOwar=SVOwar))
    print(f"... wrote {file_name}")
navigation_template = env.get_template("glavn.html")
with open("data/document.html", "w", encoding="utf-8") as f:
        f.write(navigation_template.render(SVOwar=SVOwar))
print("... wrote data/document.html")

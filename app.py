from flask import Flask, render_template, request
from bokeh.embed import components  
import create_viz as cv

app = Flask(__name__)

@app.route('/')
def show_dashboard():
    all_plots = cv.main(['likes', 'watches', 'comments'])
    script, div = components(all_plots)
    print("success")

    return render_template('index.html', script=script, div=div)

if __name__ == '__main__':
    app.run()
# ---------------------------------------------------------------------------#
# Imports
# ---------------------------------------------------------------------------#

# import json
from datetime import datetime
import dateutil.parser
import babel
from flask import (Flask, render_template, request, flash, jsonify,
                   redirect, url_for)
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
# from flask_wtf import Form
from forms import ArtistForm, ShowForm, VenueForm


# ---------------------------------------------------------------------------#
# App Config.
# ---------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)


# ---------------------------------------------------------------------------#
# Models.
# ---------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(200))
    shows = db.relationship('Show', backref='staging', lazy=True)


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(200))
    shows = db.relationship('Show', backref='performing', lazy=True)


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(
        db.Integer,
        db.ForeignKey('artists.id', ondelete="CASCADE"),
        nullable=False
    )
    venue_id = db.Column(
        db.Integer,
        db.ForeignKey('venues.id', ondelete="CASCADE"),
        nullable=False
    )
    start_time = db.Column(db.DateTime, nullable=False)


# ---------------------------------------------------------------------------#
# Filters.
# ---------------------------------------------------------------------------#

def format_datetime(value, date_format='medium'):
    date = dateutil.parser.parse(value)
    if date_format == 'full':
        date_format = "EEEE MMMM, d, y 'at' h:mma"
    elif date_format == 'medium':
        date_format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, date_format)


app.jinja_env.filters['datetime'] = format_datetime


# ---------------------------------------------------------------------------#
# Controllers.
# ---------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template(
        'pages/home.html',
        artists=Artist.query.order_by('id').limit(10).all(),
        venues=Venue.query.order_by('id').limit(10).all()
    )


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = []
    cities_with_venues = db.session.query(
        Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    for city, state in cities_with_venues:
        venues = Venue.query.filter_by(city=city, state=state).all()
        venues_by_city = {
            "city": city,
            "state": state,
            "venues": venues,
        }
        data.append(venues_by_city)
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    search_term = "%{}%".format(search_term)
    data = Venue.query.filter(Venue.name.ilike(search_term)).all()
    count = len(data)
    response = {
        "count": count,
        "data": data
    }
    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    """shows the venue page with the given venue_id"""
    venue = Venue.query.get(venue_id)

    upcoming_shows = []
    past_shows = []
    now = datetime.now()
    for show in venue.shows:
        artist = Artist.query.get(show.artist_id)
        start_time = show.start_time
        if now > start_time:
            past_shows.append({
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(start_time),
            })
        else:
            upcoming_shows.append({
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": str(start_time),
            })

    venue_with_show_info = {
        'id': venue.id,
        'name': venue.name,
        'city': venue.city,
        'state': venue.state,
        'address': venue.address,
        'phone': venue.phone,
        'genres': venue.genres,
        'website': venue.website,
        'image_link': venue.image_link,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'upcoming_shows_count': len(upcoming_shows),
        'past_shows_count': len(past_shows)
    }

    return render_template('pages/show_venue.html', venue=venue_with_show_info)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        new_venue = Venue(
            name=request.form['name'],
            city=request.form['city'],
            state=request.form['state'],
            address=request.form['address'],
            phone=request.form['phone'],
            genres=request.form.getlist('genres'),
            website=request.form['website'],
            facebook_link=request.form['facebook_link'],
            image_link=request.form['image_link'],
            seeking_talent=int(request.form['seeking_talent']),
            seeking_description=request.form['seeking_description'],
        )
        db.session.add(new_venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        # on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' + request.form['name']
              + ' could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    try:
        print('aaa')
        print("venue_id: ", venue_id)
        venue_name = Venue.query.get(venue_id).name
        print('bbb')
        print("venue_name: ", venue_name)
        Venue.query.filter_by(id=venue_id).delete()
        print('ccc')
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        # on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' + venue_name
              + ' could not be deleted.')
        return jsonify({'success': False})
    else:
        # on successful db insert, flash success
        flash('Venue ' + venue_name + ' was successfully deleted!')
        return jsonify({'success': True})


#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
    all_artists = Artist.query.order_by('name').all()
    return render_template('pages/artists.html', artists=all_artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    search_term = "%{}%".format(search_term)
    data = Artist.query.filter(Artist.name.ilike(search_term)).all()
    count = len(data)
    response = {
        "count": count,
        "data": data
    }
    return render_template(
        'pages/search_artists.html',
        results=response,
        search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    """shows the venue page with the given venue_id"""

    artist = Artist.query.get(artist_id)

    upcoming_shows = []
    past_shows = []
    now = datetime.now()
    for show in artist.shows:
        venue = Venue.query.get(show.venue_id)
        start_time = show.start_time
        if now > start_time:
            past_shows.append({
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": str(start_time),
            })
        else:
            upcoming_shows.append({
                "venue_id": venue.id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": str(start_time),
            })

    artist_with_show_info = {
        'id': artist.id,
        'name': artist.name,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'genres': artist.genres,
        'website': artist.website,
        'image_link': artist.image_link,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'upcoming_shows_count': len(upcoming_shows),
        'past_shows_count': len(past_shows)
    }

    return render_template(
        'pages/show_artist.html',
        artist=artist_with_show_info)


#  Update
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.genres = request.form.getlist('genres')
        artist.website = request.form['website']
        artist.facebook_link = request.form['facebook_link']
        artist.image_link = request.form['image_link']
        artist.seeking_venue = int(request.form['seeking_venue'])
        artist.seeking_description = request.form['seeking_description']
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        # on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' + request.form['name']
              + ' could not be edited.')
    else:
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully edited!')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.genres = request.form.getlist('genres')
        venue.website = request.form['website']
        venue.facebook_link = request.form['facebook_link']
        venue.image_link = request.form['image_link']
        venue.seeking_talent = int(request.form['seeking_talent'])
        venue.seeking_description = request.form['seeking_description']
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        # on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' + request.form['name']
              + ' could not be edited.')
    else:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully edited!')

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    try:
        print('aaa')
        new_artist = Artist(
            name=request.form['name'],
            city=request.form['city'],
            state=request.form['state'],
            phone=request.form['phone'],
            genres=request.form.getlist('genres'),
            website=request.form['website'],
            facebook_link=request.form['facebook_link'],
            image_link=request.form['image_link'],
            seeking_venue=int(request.form['seeking_venue']),
            seeking_description=request.form['seeking_description']
        )
        db.session.add(new_artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        # on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' + request.form['name']
              + ' could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    """displays list of shows at /shows"""
    data = []
    all_shows = Show.query.order_by('start_time').all()
    for show in all_shows:
        venue_name = Venue.query.get(show.venue_id).name
        artist = Artist.query.get(show.artist_id)
        show_data = {
            "venue_id": show.venue_id,
            "venue_name": venue_name,
            "artist_id": show.artist_id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(show.start_time),
        }
        data.append(show_data)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    try:
        new_show = Show(
            artist_id=request.form['artist_id'],
            venue_id=request.form['venue_id'],
            start_time=request.form['start_time']
        )
        db.session.add(new_show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        # on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Show could not be listed.')
    else:
        # on successful db insert, flash success
        flash('Show was successfully listed!')

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s '
                  '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


# ---------------------------------------------------------------------------#
# Launch.
# ---------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

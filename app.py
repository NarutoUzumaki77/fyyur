# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler

from forms import *
from flask_migrate import Migrate

from models import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    if not isinstance(value, str):
        value = str(value)
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    state = ''
    city = ''
    data = []
    _index = -1
    venues = db.session.query(Venue).order_by(Venue.state, Venue.city).all()
    utc_now = datetime.utcnow()
    for venue in venues:
        if venue.state != state and venue.city != city:
            _index += 1
            state = venue.state
            city = venue.city
            data.append({'city': city, 'state': state, 'venues': []})
            shows = db.session.query(Show).filter(Show.venue_id == venue.id).all()
            num_upcoming_shows = 0
            for show in shows:
                if show.date_time > utc_now:
                    num_upcoming_shows += 1
            data[_index]['venues'].append(
                {'id': venue.id, 'name': venue.name, 'num_upcoming_shows': num_upcoming_shows})
            db.session.close()
        elif venue.state == state and venue.city == city:
            shows = db.session.query(Show).filter(Show.venue_id == venue.id)
            num_upcoming_shows = 0
            for show in shows:
                if show.date_time > utc_now:
                    num_upcoming_shows += 1
            data[_index]['venues'].append(
                {'id': venue.id, 'name': venue.name, 'num_upcoming_shows': num_upcoming_shows})
            db.session.close()

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    response = {}
    try:
        _venues = db.session.query(Venue).filter(
            Venue.name.ilike('%{}%'.format(request.form.get('search_term', '')))).all()
        response.update({'count': len(_venues)})
        response.update({'data': _venues})
    except Exception as err:
        print(err)
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue_info = db.session.query(Show, Venue).join(Venue).filter(Venue.id == venue_id).all()
    if len(venue_info) <= 0:
        venue_info = db.session.query(Venue).filter(Venue.id == venue_id).all()
        venue = venue_info[0]
    else:
        venue = venue_info[0].Venue
    data = {
        'id': venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "city": venue.city,
        "state": venue.state,
        "address": venue.address,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        'past_shows': {},
        'upcoming_shows': {},
        'past_shows_count': 0,
        'upcoming_shows_count': 0
    }
    try:
        past_show = []
        upcoming_show = []

        for show in venue_info:
            now = datetime.utcnow()
            show_time = show.Show.date_time
            artist = Artist.query.get(show.Show.artist_id)
            if show_time > now:
                upcoming_show.append({
                    'artist_id': artist.id,
                    'artist_name': artist.name,
                    'artist_image_link': artist.image_link,
                    "start_time": show.Show.date_time
                })
            else:
                past_show.append({
                    'artist_id': artist.id,
                    'artist_name': artist.name,
                    'artist_image_link': artist.image_link,
                    "start_time": show.Show.date_time
                })

        data.update({'past_shows': past_show})
        data.update({'upcoming_shows': upcoming_show})
        data.update({'past_shows_count': len(past_show)})
        data.update({'upcoming_shows_count': len(upcoming_show)})
    except:
        # pass silently if venue has no record in the Show table
        pass

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    try:
        name = form.name.data
        city = form.city.data
        state = form.state.data
        phone = form.phone.data
        genres = form.genres.data
        image_link = form.image_link.data
        address = form.address.data
        website = form.website.data
        seeking_talent = form.seeking_talent.data
        seeking_description = form.seeking_description.data
        facebook_link = form.facebook_link.data
        venue = Venue(
            name=name,
            city=city,
            state=state,
            phone=phone,
            genres=genres,
            address=address,
            facebook_link=facebook_link,
            image_link=image_link,
            website=website,
            seeking_talent=seeking_talent,
            seeking_description=seeking_description
        )
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + form.name.data + ' was successfully listed!')
    except Exception as err:
        db.session.rollback()
        flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
        print(err)
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
    try:
        venue = db.session.query(Venue).get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('Successfully deleted venue {}'.format(venue.name))
    except Exception as err:
        db.session.rollback()
        print(err)
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = {}
    try:
        data = db.session.query(Artist).order_by(Artist.id).all()
        db.session.close()
    except Exception as err:
        print(err)
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    response = {}
    try:
        search_artist = db.session.query(Artist).filter(
            Artist.name.ilike('%{}%'.format(request.form.get('search_term', '')))).all()
        response.update({'count': len(search_artist)})
        response.update({'data': search_artist})
    except Exception as err:
        print(err)
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist_info = db.session.query(Show, Artist).join(Artist).filter(Artist.id == artist_id).all()
    if len(artist_info) <= 0:
        artist_info = db.session.query(Artist).filter(Artist.id == artist_id).all()
        artist = artist_info[0]
    else:
        artist = artist_info[0].Artist
    data = {
        'id': artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        'past_show': {},
        'upcoming_show': {},
        'past_shows_count': 0,
        'upcoming_shows_count': 0
    }
    try:
        past_show = []
        upcoming_show = []

        for show in artist_info:
            now = datetime.utcnow()
            show_time = show.Show.date_time
            venue = Venue.query.get(show.Show.venue_id)
            if show_time > now:
                upcoming_show.append({
                    'venue_id': venue.id,
                    'venue_name': venue.name,
                    'venue_image_link': venue.image_link,
                    "start_time": show.Show.date_time
                })
            else:
                past_show.append({
                    'venue_id': venue.id,
                    'venue_name': venue.name,
                    'venue_image_link': venue.image_link,
                    "start_time": show.Show.date_time
                })

        data.update({'past_show': past_show})
        data.update({'upcoming_show': upcoming_show})
        data.update({'past_shows_count': len(past_show)})
        data.update({'upcoming_shows_count': len(upcoming_show)})
    except:
        # pass silently if artist has no record in the Show table
        pass

    return render_template('pages/show_artist.html', artist=data)


#  ----------------------------------------------------------------
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = db.session.query(Artist).get(artist_id)
    if artist:
        form.name.data = artist.name
        form.city.data = artist.city
        form.state.data = artist.state
        form.phone.data = artist.phone
        form.genres.data = artist.genres
        form.facebook_link.data = artist.facebook_link
        form.image_link.data = artist.image_link
        form.website.data = artist.website
        form.seeking_venue.data = artist.seeking_venue
        form.seeking_description.data = artist.seeking_description

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()

    artist = db.session.query(Artist).get(artist_id)
    if artist:
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        artist.website = form.website.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data

        db.session.commit()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    venue = db.session.query(Venue).get(venue_id)
    if venue:
        form.name.data = venue.name
        form.city.data = venue.city
        form.state.data = venue.state
        form.phone.data = venue.phone
        form.genres.data = venue.genres
        form.image_link.data = venue.image_link
        form.address.data = venue.address
        form.website.data = venue.website
        form.seeking_talent.data = venue.seeking_talent
        form.seeking_description.data = venue.seeking_description
        form.facebook_link.data = venue.facebook_link

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm()

    venue = db.session.query(Venue).get(venue_id)
    if venue:
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.phone = form.phone.data
        venue.genres = form.genres.data
        venue.image_link = form.image_link.data
        venue.address = form.address.data
        venue.website = form.website.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        venue.facebook_link = form.facebook_link.data

        db.session.commit()
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()
    try:
        name = form.name.data
        city = form.city.data
        state = form.state.data
        phone = form.phone.data
        genres = form.genres.data
        facebook_link = form.facebook_link.data
        image_link = form.image_link.data
        website = form.website.data
        seeking_venue = form.seeking_venue.data
        seeking_description = form.seeking_description.data
        artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            genres=genres,
            facebook_link=facebook_link,
            image_link=image_link,
            website=website,
            seeking_venue=seeking_venue,
            seeking_description=seeking_description
        )
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as err:
        db.session.rollback()
        flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
        print(err)
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  ----------------------------------------------------------------
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = {}
    try:
        data = db.session.query(Show, Venue, Artist).join(Venue).join(Artist).all()
    except Exception as err:
        print(err)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm()
    try:
        artist_id = form.artist_id.data
        venue_id = form.venue_id.data
        start_time = form.start_time.data
        show = Show(
            artist_id=artist_id,
            venue_id=venue_id,
            date_time=start_time
        )
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except Exception as err:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
        print(err)
    finally:
        db.session.close()
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
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

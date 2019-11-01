from sqlalchemy import String

from app import db


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String())
    genres = db.Column(db.ARRAY(String()))
    venue = db.relationship("Show", backref='venue')

    def __repr__(self):
        return f'<Venue {self.id}, {self.name}, {self.city}, {self.state}, {self.address}, {self.phone}, ' \
               f'{self.image_link}, {self.facebook_link}, {self.website}, {self.seeking_talent}, ' \
               f'{self.seeking_description}, {self.genres}>'


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String())
    website = db.Column(db.String(500))
    artist = db.relationship("Show", backref="artist")

    def __repr__(self):
        return f'<Artist {self.id}, {self.name}, {self.city}, {self.state}, {self.phone}, ' \
               f'{self.image_link}, {self.facebook_link}, {self.website}, {self.seeking_venue}, ' \
               f'{self.seeking_description}, {self.genres}>'


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)

    def __repr__(self):
        return f'<Show {self.id}, {self.date_time}, {self.artist_id}, {self.venue_id}'
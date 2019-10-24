# /usr/bin/env python3
"""Relational database model to store web search data"""
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, MetaData
from sqlalchemy import String, Table

metadata = MetaData()


t_aggregate = Table(
    'aggregate', metadata,
    Column('search_type', String(5), primary_key=True),
    Column('date', DateTime, primary_key=True),
    Column('device', String(10), primary_key=True),
    Column('country', String(3), primary_key=True),
    Column('clicks', Integer, nullable=False),
    Column('impressions', Integer, nullable=False),
    Column('ctr', Float, nullable=False),
    Column('average_position', Float, nullable=False),
)

t_breakdown = Table(
    'breakdown', metadata,
    Column('search_type', String(5), primary_key=True),
    Column('date', DateTime, primary_key=True),
    Column('device', String(10), primary_key=True),
    Column('country', String(3), primary_key=True),
    Column('url', String(255), primary_key=True),
    Column('query', String(255), primary_key=True),
    Column('secondary_result', Boolean, primary_key=True),
    Column('clicks', Integer, nullable=False),
    Column('impressions', Integer, nullable=False),
    Column('ctr', Float, nullable=False),
    Column('average_position', Float, nullable=False),
)

t_search_appearance = Table(
    'search_appearance', metadata,
    Column('search_type', String(5), primary_key=True),
    Column('date', DateTime, primary_key=True),
    Column('appearance', String(128), primary_key=True),
    Column('clicks', Integer, nullable=False),
    Column('impressions', Integer, nullable=False),
    Column('ctr', Float, nullable=False),
    Column('average_position', Float, nullable=False),
)

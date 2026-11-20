from sqlalchemy import Column,Integer,BigInteger,String,JSON,Text,Date,DateTime,ForeignKey,UniqueConstraint
from src.config.database import Base
class User(Base):
 __tablename__='users'
 id=Column(Integer,primary_key=True);email=Column(String(100),unique=True,nullable=False);password=Column(String(200));role=Column(String(20))
class Settlement(Base):
 __tablename__='settlements'
 id=Column(Integer,primary_key=True);code=Column(String(60),unique=True,nullable=False);day=Column(String(10));venue=Column(String(40));play=Column(String(60));channel=Column(String(30));gross_cents=Column(BigInteger);refund_cents=Column(BigInteger);fee_cents=Column(BigInteger);seats=Column(Integer);checked=Column(Integer)
class Pivot(Base):
 __tablename__='pivots'
 id=Column(Integer,primary_key=True);name=Column(String(100));row_dim=Column(String(30));col_dim=Column(String(30));state=Column(String(20),default='queued');result=Column(JSON,nullable=True);error=Column(Text,default='')
class Review(Base):
 __tablename__='reviews'
 id=Column(Integer,primary_key=True);pivot_id=Column(Integer,ForeignKey('pivots.id'));row_key=Column(String(100));col_key=Column(String(100));book_cents=Column(BigInteger);expected_cents=Column(BigInteger);difference_cents=Column(BigInteger);note=Column(Text);status=Column(String(20),default='draft')
class Audit(Base):
 __tablename__='audits'
 id=Column(Integer,primary_key=True);actor=Column(String(100));action=Column(String(200));created=Column(String(40))
class ShowSession(Base):
 __tablename__='show_sessions'
 id=Column(Integer,primary_key=True);code=Column(String(60),unique=True,nullable=False);play=Column(String(60),nullable=False);venue=Column(String(40),nullable=False);show_day=Column(Date,nullable=False);capacity=Column(Integer,nullable=False)
class SalesReport(Base):
 __tablename__='sales_reports'
 id=Column(Integer,primary_key=True);session_id=Column(Integer,ForeignKey('show_sessions.id'),nullable=False);report_day=Column(Date,nullable=False);sold_total=Column(Integer,nullable=False);available_seats=Column(Integer,nullable=False);received_at=Column(DateTime,nullable=False);updated_at=Column(DateTime,nullable=False)
 __table_args__=(UniqueConstraint('session_id','report_day',name='uq_session_report_day'),)
class WarningBatch(Base):
 __tablename__='warning_batches'
 id=Column(Integer,primary_key=True);name=Column(String(100));cutoff_at=Column(DateTime,nullable=False);state=Column(String(20),default='queued');result=Column(JSON,nullable=True);error=Column(Text,default='')

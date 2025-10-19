from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import Query, Request
from contextlib import asynccontextmanager
from sqlalchemy import or_
import razorpay
import hmac, hashlib, json
import os
# test_app.py
from main import SQLModel
SQLModel.metadata.clear()

# ================================
# CONFIG
# ================================
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "your_key_id")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "your_key_secret")
DATABASE_URL = "sqlite:///./tourism.db"
engine = create_engine(DATABASE_URL, echo=True)

# ================================
# DB Models
# ================================
from sqlmodel import SQLModel, Field

class Attraction(SQLModel, table=True):
    __tablename__ = "attraction"
    __table_args__ = {"extend_existing": True}  # ✅ add this

    id: int = Field(default=None, primary_key=True)
    name: str
    location: str
    description: str
    historical_background: Optional[str] = None
    scenic_spots: Optional[str] = None
    nearby_restaurants_hotels: Optional[str] = None
    entry_fee: Optional[str] = None
    food_cost_range: Optional[str] = None
    travel_cost_estimate: Optional[str] = None
    stay_cost_per_night: Optional[str] = None
    best_time_visit: Optional[str] = None

class TouristBooking(SQLModel, table=True):
    __tablename__ = "tourist_bookings"
    id: Optional[int] = Field(default=None, primary_key=True)
    tourist_name: str = Field(index=True)
    email: str = Field(index=True)
    package: str
    amount: float
    currency: str = "INR"
    order_id: str = Field(unique=True)
    payment_id: Optional[str] = None
    status: str = "PENDING"


class AttractionCreate(SQLModel):
    name: str
    description: Optional[str] = None
    historical_background: Optional[str] = None
    scenic_spots: Optional[str] = None
    nearby_restaurants_hotels: Optional[str] = None
    entry_fee: Optional[str] = None
    food_cost_range: Optional[str] = None
    travel_cost_estimate: Optional[str] = None
    stay_cost_per_night: Optional[str] = None
    best_time_visit: Optional[str] = None


class AttractionRead(Attraction):
    pass

class AttractionUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    historical_background: Optional[str] = None
    scenic_spots: Optional[str] = None
    nearby_restaurants_hotels: Optional[str] = None
    entry_fee: Optional[str] = None
    food_cost_range: Optional[str] = None
    travel_cost_estimate: Optional[str] = None
    stay_cost_per_night: Optional[str] = None
    best_time_visit: Optional[str] = None

class User(SQLModel, table=True):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    
class Booking(SQLModel, table=True):
    __tablename__ = "booking"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    attraction_id: int
    date: str



def get_session():
    with Session(engine) as session:
        yield session

def seed_data():
   
   sample = [
        {"name": "Baba Baidyanath Temple, Deoghar", "description": "One of the 12 Jyotirlingas, a major Shiva temple and pilgrimage center.", "historical_background": "Linked to Hindu mythology; center of faith for centuries.", "scenic_spots": "Nandan Pahar hills with panoramic views.", "nearby_restaurants_hotels": "Shree Mithila Bhojnalaya, Hotel Satyam", "entry_fee": "₹60", "food_cost_range": "150 – 400", "travel_cost_estimate": "500 – 1500", "stay_cost_per_night": "600 – 1200", "best_time_visit": "July–Aug (Shravan Mela) & Oct–Feb | 4:00 AM – 9:00 PM"},
        {"name": "Parasnath Hill (Shikharji)", "description": "Highest peak in Jharkhand, sacred for Jains with temples.", "historical_background": "Named after Parshvanatha (23rd Jain Tirthankara); pilgrimage site for 2,000+ years.", "scenic_spots": "Trek routes and summit with breathtaking views.", "nearby_restaurants_hotels": "Local eateries in Isri Bazaar, dharamshalas, guest houses", "entry_fee": "₹20 – 50", "food_cost_range": "100 – 250", "travel_cost_estimate": "600 – 2000", "stay_cost_per_night": "400 – 800", "best_time_visit": "Oct–March (trekking season) | Sunrise – Sunset"},
        {"name": "Dassam Falls, Ranchi", "description": "Spectacular waterfall on the Kanchi River, natural scenic beauty.", "historical_background": "Cultural significance for tribal communities.", "scenic_spots": "Base and top viewpoints for photography.", "nearby_restaurants_hotels": "Local Ranchi eateries, city hotels", "entry_fee": "₹10 – 30", "food_cost_range": "200 – 500", "travel_cost_estimate": "300 – 1200", "stay_cost_per_night": "800 – 2000", "best_time_visit": "Aug–Feb (post-monsoon) | Sunrise – Sunset"},
        {"name": "Rajrappa Temple", "description": "Temple of Goddess Chhinnamasta at river confluence.", "historical_background": "Ancient site linked to tribal practices; Hindu temple added later.", "scenic_spots": "Temple architecture & river confluence views.", "nearby_restaurants_hotels": "Local restaurants near Rajrappa", "entry_fee": "₹0", "food_cost_range": "100 – 300", "travel_cost_estimate": "400 – 1500", "stay_cost_per_night": "500 – 1000", "best_time_visit": "Oct–March & Navratri | 6:00 AM – 6:00 PM"},
        {"name": "Seraikela Palace & Rajmahal Hills", "description": "Palace exhibits tribal art & Chhau dance; hills of geological & historical significance.", "historical_background": "Palace belongs to royal family; hills date to ancient formations.", "scenic_spots": "Palace courtyards & hill landscapes.", "nearby_restaurants_hotels": "Local eateries in Seraikela town", "entry_fee": "₹20 – 50", "food_cost_range": "150 – 350", "travel_cost_estimate": "600 – 1800", "stay_cost_per_night": "700 – 1500", "best_time_visit": "Nov–Feb | 10:00 AM – 5:00 PM (Palace, closed Mondays); Hills open all day"},
        {"name": "Itkhori: Harihar Dham (Khori Mandir)", "description": "A famous Shiva temple with the world's largest Shivlinga.", "historical_background": "Believed to be visited by Goddess Maa Sheetla & associated with Lord Buddha.", "scenic_spots": "Temple complex and surrounding greenery.", "nearby_restaurants_hotels": "Local eateries in Itkhori town", "entry_fee": "₹40 – 65", "food_cost_range": "100 – 250", "travel_cost_estimate": "500 – 1500", "stay_cost_per_night": "500 – 900", "best_time_visit": "Feb–April (Shivratri) & July–Aug (Shravan) | 4:30 AM – 9:00 PM"},
        {"name": "Birikitti Fort and Baradari of Rajmahal", "description": "Historic ruins and Mughal architecture showcasing regional history.", "historical_background": "Once part of Mughal and Bengal Sultanate stronghold.", "scenic_spots": "Ancient fort walls, Rajmahal Baradari viewpoints.", "nearby_restaurants_hotels": "Small eateries in Rajmahal town", "entry_fee": "₹10 – 30", "food_cost_range": "100 – 300", "travel_cost_estimate": "600 – 2000", "stay_cost_per_night": "600 – 1000", "best_time_visit": "Oct–March | 9:00 AM – 6:00 PM"},
        {"name": "Rankini Temple, Jadugora", "description": "A powerful Shaktipeeth dedicated to Goddess Rankini.", "historical_background": "Associated with tribal traditions and Shakti worship.", "scenic_spots": "Temple complex & surrounding forests.", "nearby_restaurants_hotels": "Local dhabas in Jadugora town", "entry_fee": "₹30", "food_cost_range": "80 – 200", "travel_cost_estimate": "400 – 1200", "stay_cost_per_night": "500 – 900", "best_time_visit": "Oct–Feb & Navratri | 6:00 AM – 7:00 PM"},
        {"name": "Ghatshila", "description": "Scenic town on the banks of Subarnarekha River, famous for natural beauty.", "historical_background": "Known for tribal culture and association with writer Bibhutibhushan Bandyopadhyay.", "scenic_spots": "Subarnarekha riverbanks, Dharagiri Falls, Phuldungri hills.", "nearby_restaurants_hotels": "Local lodges & eateries in Ghatshila", "entry_fee": "₹40", "food_cost_range": "150 – 400", "travel_cost_estimate": "500 – 1500", "stay_cost_per_night": "600 – 1200", "best_time_visit": "Nov–Feb & Monsoon (for waterfalls) | Open all day"},
        {"name": "Dalma Wildlife Sanctuary", "description": "Sanctuary famous for elephants, leopards, and trekking routes.", "historical_background": "Established in 1975, inaugurated by Sanjay Gandhi.", "scenic_spots": "Dalma Hills, trekking trails, wildlife safari.", "entry_fee": "₹20 – 50", "travel_cost_estimate": "500 – 2000", "best_time_visit": "Oct–March (pleasant weather) | Sunrise – Sunset"},
        {"name": "Saranda Forest", "description": "Asia’s largest Sal forest, rich in biodiversity.", "historical_background": "Tribal habitation for centuries; name means 'Land of Seven Hundred Hills'.", "scenic_spots": "Dense Sal trees, hill ranges, streams.", "entry_fee": "₹10 – 30", "travel_cost_estimate": "600 – 2200", "best_time_visit": "Nov–Feb (cool climate) | All day"},
        {"name": "Jonha Falls (Gautamdhara)", "description": "Picturesque waterfall near Ranchi, also known as Gautamdhara.", "historical_background": "Associated with Lord Buddha’s meditation site.", "scenic_spots": "Waterfall base & surrounding forest.", "entry_fee": "₹10 – 20", "travel_cost_estimate": "400 – 1500", "best_time_visit": "July–Feb (post-monsoon) | Sunrise – Sunset"},
        {"name": "Palamu Tiger Reserve", "description": "One of India’s first nine tiger reserves under Project Tiger.", "historical_background": "Established in 1973, part of Betla National Park.", "scenic_spots": "Tiger safari, Betla Fort ruins, dense forests.", "entry_fee": "₹50 – 200", "travel_cost_estimate": "800 – 2500", "best_time_visit": "Nov–March | Sunrise – Sunset"},
        {"name": "Topchanchi Wildlife Sanctuary", "description": "Sanctuary around Topchanchi Lake, home to migratory birds and wildlife.", "historical_background": "Lake built during British era for water supply.", "scenic_spots": "Topchanchi Lake, forest trails, birdwatching.", "entry_fee": "₹20 – 50", "travel_cost_estimate": "400 – 1500", "best_time_visit": "Oct–Feb (bird season) | Sunrise – Sunset"},
        {"name": "Netarhat", "description": "Queen of Chotanagpur plateau known for pine forests and sunrise/sunset points.", "historical_background": "Developed during the British period as a hill station; home to the renowned Netarhat Residential School (est. 1954).", "scenic_spots": "Sunrise Point, Magnolia Sunset Point, Pine forests, Koel View Point, Upper/Lower Ghaghri Falls (nearby).", "nearby_restaurants_hotels": "Netarhat Tourist Lodge, Prabhat Vihar, local dhabas", "entry_fee": "₹30 – 50 (viewpoints)", "food_cost_range": "150 – 400", "travel_cost_estimate": "800 – 2200", "stay_cost_per_night": "800 – 2000", "best_time_visit": "Oct–March; also Monsoon for waterfalls | All day"},
        {"name": "Patratu Valley", "description": "Scenic valley roads with sweeping hairpin bends and reservoir views near Ranchi.", "historical_background": "Valley developed around the Patratu Dam (constructed in the 1960s) supporting the Patratu Thermal Power Station.", "scenic_spots": "Patratu Dam & Reservoir, valley viewpoints, serpentine ghat roads, lakeside promenade.", "nearby_restaurants_hotels": "Patratu Lake Resort, lakeside cafes, local eateries", "entry_fee": "₹25 – 50 (promenade/parking)", "food_cost_range": "120 – 350", "travel_cost_estimate": "500 – 1500", "stay_cost_per_night": "1200 – 2500", "best_time_visit": "Oct–Feb (clear views); evenings for sunset | Sunrise – Sunset"},
        {"name": "Hazaribagh Lake", "description": "Serene urban lake with walking paths; gateway to Hazaribagh National Park.", "historical_background": "Constructed during the British era as a series of interconnected artificial lakes in Hazaribagh town.", "scenic_spots": "Lakeside promenade, boating area, viewpoints; national park and Canary Hill nearby.", "nearby_restaurants_hotels": "Local eateries around Lake Road, town hotels and lodges", "entry_fee": "₹10 – 20", "food_cost_range": "120 – 300", "travel_cost_estimate": "400 – 1200", "stay_cost_per_night": "700 – 1500", "best_time_visit": "Oct–Feb (pleasant weather); evenings for sunset | 6:00 AM – 8:00 PM"},
    ]

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables...")
    SQLModel.metadata.create_all(engine)
    seed_data()
    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

# ================================
# CORS CONFIGURATION
# ================================
origins = [
    "http://127.0.0.1:5501",  # Your frontend dev environment
    "http://localhost:5501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# Razorpay Client Setup
# ================================
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# ================================
# ROUTES
# ================================
@app.get("/")
def root():
    return {"message": "Server is running"}


@app.post("/create_order")
async def create_order(
    tourist_name: str = Form(...),
    email: str = Form(...),
    package: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_session)
):
    if not RAZORPAY_KEY_ID or RAZORPAY_KEY_ID == "your_key_id":
        raise HTTPException(status_code=500, detail="Razorpay keys not configured on the server.")
    amount_paise = int(amount * 100)
    try:
        order = razorpay_client.order.create({"amount": amount_paise, "currency": "INR", "payment_capture": 1})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Razorpay error: {e}")

    booking = TouristBooking(
        tourist_name=tourist_name,
        email=email,
        package=package,
        amount=amount,
        order_id=order["id"]
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {
        "order_id": order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "key": RAZORPAY_KEY_ID,
        "booking_id": booking.id,
        "prefill": {"name": tourist_name, "email": email}
    }


@app.post("/verify_payment")
async def verify_payment(request: Request, db: Session = Depends(get_session)):
    data = await request.json()
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        raise HTTPException(status_code=400, detail="Missing Razorpay payment details.")

    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Payment verification failed: Invalid signature.")

    booking = db.exec(select(TouristBooking).where(TouristBooking.order_id == razorpay_order_id)).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found for this order.")
    booking.payment_id = razorpay_payment_id
    booking.status = "PAID"
    db.add(booking)
    db.commit()
    return {"status": "success", "message": "Payment verified successfully", "order_id": razorpay_order_id}


@app.get("/attractions", response_model=List[AttractionRead])
def get_attractions(q: Optional[str] = Query(None), db: Session = Depends(get_session)):
    statement = select(Attraction)
    if q:
        statement = statement.where(
            or_(
                Attraction.name.contains(q),
                Attraction.description.contains(q)
            )
        )
    return db.exec(statement).all()


@app.get("/attractions/{attraction_id}", response_model=AttractionRead)
def get_attraction(attraction_id: int, db: Session = Depends(get_session)):
    attraction = db.get(Attraction, attraction_id)
    if not attraction:
        raise HTTPException(status_code=404, detail="Attraction not found")
    return attraction


@app.post("/attractions", response_model=AttractionRead)
def create_attraction(attraction: AttractionCreate, db: Session = Depends(get_session)):
    db_attraction = Attraction.from_orm(attraction)
    db.add(db_attraction)
    db.commit()
    db.refresh(db_attraction)
    return db_attraction


@app.put("/attractions/{attraction_id}", response_model=AttractionRead)
def update_attraction(attraction_id: int, data: AttractionUpdate, db: Session = Depends(get_session)):
    db_attraction = db.get(Attraction, attraction_id)
    if not db_attraction:
        raise HTTPException(status_code=404, detail="Attraction not found")
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_attraction, key, value)
    db.add(db_attraction)
    db.commit()
    db.refresh(db_attraction)
    return db_attraction


@app.delete("/attractions/{attraction_id}")
def delete_attraction(attraction_id: int, db: Session = Depends(get_session)):
    attraction = db.get(Attraction, attraction_id)
    if not attraction:
        raise HTTPException(status_code=404, detail="Attraction not found")
    db.delete(attraction)
    db.commit()
    return {"ok": True}


@app.get("/destinations")
def get_destinations():
    return {"destinations": [{"id": 1, "name": "Ranchi"}, {"id": 2, "name": "Jamshedpur"}, {"id": 3, "name": "Dhanbad"}, {"id": 4, "name": "Hazaribagh"}]}


@app.post("/attractions", response_model=AttractionRead)
def create_attraction(attraction: AttractionCreate, db: Session = Depends(get_session)):
    db_attraction = Attraction.from_orm(attraction)
    db.add(db_attraction)
    db.commit()
    db.refresh(db_attraction)
    return db_attraction


@app.put("/attractions/{attraction_id}", response_model=AttractionRead)
def update_attraction(attraction_id: int, data: AttractionUpdate, db: Session = Depends(get_session)):
    db_attraction = db.get(Attraction, attraction_id)
    if not db_attraction:
        raise HTTPException(status_code=404, detail="Attraction not found")
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_attraction, key, value)
    db.add(db_attraction)
    db.commit()
    db.refresh(db_attraction)
    return db_attraction


@app.delete("/attractions/{attraction_id}")
def delete_attraction(attraction_id: int, db: Session = Depends(get_session)):
    attraction = db.get(Attraction, attraction_id)
    if not attraction:
        raise HTTPException(status_code=404, detail="Attraction not found")
    db.delete(attraction)
    db.commit()
    return {"ok": True}



from typing import Optional, List
from sqlmodel import Field, SQLModel, create_engine, Session, select
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# ================================
# CONFIG
# ================================
DATABASE_URL = "sqlite:///./tourism.db"
engine = create_engine(DATABASE_URL, echo=True)

# ================================
# DB Models
# ================================
class Attraction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None

# ================================
# FastAPI App Setup
# ================================
app = FastAPI()

# Allow all origins for now (for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# Database Session Dependency
# ================================
def get_session():
    with Session(engine) as session:
        yield session

# ================================
# Routes
# ================================
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/attractions", response_model=List[Attraction])
def read_attractions(session: Session = Depends(get_session)):
    attractions = session.exec(select(Attraction)).all()
    return attractions


from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}


# from typing import Optional, List
# from sqlmodel import Field, SQLModel, create_engine, Session, select
# from fastapi import FastAPI, HTTPException, Query, Request, Form, Depends
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager
# from sqlalchemy import or_
# import razorpay
# import hmac, hashlib, json
# import os

# # ================================
# # CONFIG
# # ================================
# # IMPORTANT: Replace with your actual Razorpay keys
# RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "your_key_id")
# RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "your_key_secret")

# DATABASE_URL = "sqlite:///./tourism.db"
# engine = create_engine(DATABASE_URL, echo=True)

# # ================================
# # DB Models
# # ================================
# class Attraction(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str
#     description: Optional[str] = None
#     historical_background: Optional[str] = None
#     scenic_spots: Optional[str] = None
#     nearby_restaurants_hotels: Optional[str] = None
#     entry_fee: Optional[str] = None
#     food_cost_range: Optional[str] = None
#     travel_cost_estimate: Optional[str] = None
#     stay_cost_per_night: Optional[str] = None
#     best_time_visit: Optional[str] = None


# class TouristBooking(SQLModel, table=True):
#     _tablename_ = "tourist_bookings"
#     id: Optional[int] = Field(default=None, primary_key=True)
#     tourist_name: str = Field(index=True)
#     email: str = Field(index=True)
#     package: str
#     amount: float
#     currency: str = "INR"
#     order_id: str = Field(unique=True)
#     payment_id: Optional[str] = None
#     status: str = "PENDING"  # PENDING, PAID, FAILED


# class AttractionCreate(SQLModel):
#     name: str
#     description: Optional[str] = None
#     historical_background: Optional[str] = None
#     scenic_spots: Optional[str] = None
#     nearby_restaurants_hotels: Optional[str] = None
#     entry_fee: Optional[str] = None
#     food_cost_range: Optional[str] = None
#     travel_cost_estimate: Optional[str] = None
#     stay_cost_per_night: Optional[str] = None
#     best_time_visit: Optional[str] = None


# class AttractionRead(Attraction):
#     pass

# class AttractionUpdate(SQLModel):
#     name: Optional[str] = None
#     description: Optional[str] = None
#     historical_background: Optional[str] = None
#     scenic_spots: Optional[str] = None
#     nearby_restaurants_hotels: Optional[str] = None
#     entry_fee: Optional[str] = None
#     food_cost_range: Optional[str] = None
#     travel_cost_estimate: Optional[str] = None
#     stay_cost_per_night: Optional[str] = None
#     best_time_visit: Optional[str] = None


# def get_session():
#     with Session(engine) as session:
#         yield session


# def seed_data():
#     sample = [
#         {"name": "Baba Baidyanath Temple, Deoghar", "description": "One of the 12 Jyotirlingas, a major Shiva temple and pilgrimage center.", "historical_background": "Linked to Hindu mythology; center of faith for centuries.", "scenic_spots": "Nandan Pahar hills with panoramic views.", "nearby_restaurants_hotels": "Shree Mithila Bhojnalaya, Hotel Satyam", "entry_fee": "₹60", "food_cost_range": "150 – 400", "travel_cost_estimate": "500 – 1500", "stay_cost_per_night": "600 – 1200", "best_time_visit": "July–Aug (Shravan Mela) & Oct–Feb | 4:00 AM – 9:00 PM"},
#         {"name": "Parasnath Hill (Shikharji)", "description": "Highest peak in Jharkhand, sacred for Jains with temples.", "historical_background": "Named after Parshvanatha (23rd Jain Tirthankara); pilgrimage site for 2,000+ years.", "scenic_spots": "Trek routes and summit with breathtaking views.", "nearby_restaurants_hotels": "Local eateries in Isri Bazaar, dharamshalas, guest houses", "entry_fee": "₹20 – 50", "food_cost_range": "100 – 250", "travel_cost_estimate": "600 – 2000", "stay_cost_per_night": "400 – 800", "best_time_visit": "Oct–March (trekking season) | Sunrise – Sunset"},
#         {"name": "Dassam Falls, Ranchi", "description": "Spectacular waterfall on the Kanchi River, natural scenic beauty.", "historical_background": "Cultural significance for tribal communities.", "scenic_spots": "Base and top viewpoints for photography.", "nearby_restaurants_hotels": "Local Ranchi eateries, city hotels", "entry_fee": "₹10 – 30", "food_cost_range": "200 – 500", "travel_cost_estimate": "300 – 1200", "stay_cost_per_night": "800 – 2000", "best_time_visit": "Aug–Feb (post-monsoon) | Sunrise – Sunset"},
#         {"name": "Rajrappa Temple", "description": "Temple of Goddess Chhinnamasta at river confluence.", "historical_background": "Ancient site linked to tribal practices; Hindu temple added later.", "scenic_spots": "Temple architecture & river confluence views.", "nearby_restaurants_hotels": "Local restaurants near Rajrappa", "entry_fee": "₹0", "food_cost_range": "100 – 300", "travel_cost_estimate": "400 – 1500", "stay_cost_per_night": "500 – 1000", "best_time_visit": "Oct–March & Navratri | 6:00 AM – 6:00 PM"},
#         {"name": "Seraikela Palace & Rajmahal Hills", "description": "Palace exhibits tribal art & Chhau dance; hills of geological & historical significance.", "historical_background": "Palace belongs to royal family; hills date to ancient formations.", "scenic_spots": "Palace courtyards & hill landscapes.", "nearby_restaurants_hotels": "Local eateries in Seraikela town", "entry_fee": "₹20 – 50", "food_cost_range": "150 – 350", "travel_cost_estimate": "600 – 1800", "stay_cost_per_night": "700 – 1500", "best_time_visit": "Nov–Feb | 10:00 AM – 5:00 PM (Palace, closed Mondays); Hills open all day"},
#         {"name": "Itkhori: Harihar Dham (Khori Mandir)", "description": "A famous Shiva temple with the world's largest Shivlinga.", "historical_background": "Believed to be visited by Goddess Maa Sheetla & associated with Lord Buddha.", "scenic_spots": "Temple complex and surrounding greenery.", "nearby_restaurants_hotels": "Local eateries in Itkhori town", "entry_fee": "₹40 – 65", "food_cost_range": "100 – 250", "travel_cost_estimate": "500 – 1500", "stay_cost_per_night": "500 – 900", "best_time_visit": "Feb–April (Shivratri) & July–Aug (Shravan) | 4:30 AM – 9:00 PM"},
#         {"name": "Birikitti Fort and Baradari of Rajmahal", "description": "Historic ruins and Mughal architecture showcasing regional history.", "historical_background": "Once part of Mughal and Bengal Sultanate stronghold.", "scenic_spots": "Ancient fort walls, Rajmahal Baradari viewpoints.", "nearby_restaurants_hotels": "Small eateries in Rajmahal town", "entry_fee": "₹10 – 30", "food_cost_range": "100 – 300", "travel_cost_estimate": "600 – 2000", "stay_cost_per_night": "600 – 1000", "best_time_visit": "Oct–March | 9:00 AM – 6:00 PM"},
#         {"name": "Rankini Temple, Jadugora", "description": "A powerful Shaktipeeth dedicated to Goddess Rankini.", "historical_background": "Associated with tribal traditions and Shakti worship.", "scenic_spots": "Temple complex & surrounding forests.", "nearby_restaurants_hotels": "Local dhabas in Jadugora town", "entry_fee": "₹30", "food_cost_range": "80 – 200", "travel_cost_estimate": "400 – 1200", "stay_cost_per_night": "500 – 900", "best_time_visit": "Oct–Feb & Navratri | 6:00 AM – 7:00 PM"},
#         {"name": "Ghatshila", "description": "Scenic town on the banks of Subarnarekha River, famous for natural beauty.", "historical_background": "Known for tribal culture and association with writer Bibhutibhushan Bandyopadhyay.", "scenic_spots": "Subarnarekha riverbanks, Dharagiri Falls, Phuldungri hills.", "nearby_restaurants_hotels": "Local lodges & eateries in Ghatshila", "entry_fee": "₹40", "food_cost_range": "150 – 400", "travel_cost_estimate": "500 – 1500", "stay_cost_per_night": "600 – 1200", "best_time_visit": "Nov–Feb & Monsoon (for waterfalls) | Open all day"},
#         {"name": "Dalma Wildlife Sanctuary", "description": "Sanctuary famous for elephants, leopards, and trekking routes.", "historical_background": "Established in 1975, inaugurated by Sanjay Gandhi.", "scenic_spots": "Dalma Hills, trekking trails, wildlife safari.", "entry_fee": "₹20 – 50", "travel_cost_estimate": "500 – 2000", "best_time_visit": "Oct–March (pleasant weather) | Sunrise – Sunset"},
#         {"name": "Saranda Forest", "description": "Asia’s largest Sal forest, rich in biodiversity.", "historical_background": "Tribal habitation for centuries; name means 'Land of Seven Hundred Hills'.", "scenic_spots": "Dense Sal trees, hill ranges, streams.", "entry_fee": "₹10 – 30", "travel_cost_estimate": "600 – 2200", "best_time_visit": "Nov–Feb (cool climate) | All day"},
#         {"name": "Jonha Falls (Gautamdhara)", "description": "Picturesque waterfall near Ranchi, also known as Gautamdhara.", "historical_background": "Associated with Lord Buddha’s meditation site.", "scenic_spots": "Waterfall base & surrounding forest.", "entry_fee": "₹10 – 20", "travel_cost_estimate": "400 – 1500", "best_time_visit": "July–Feb (post-monsoon) | Sunrise – Sunset"},
#         {"name": "Palamu Tiger Reserve", "description": "One of India’s first nine tiger reserves under Project Tiger.", "historical_background": "Established in 1973, part of Betla National Park.", "scenic_spots": "Tiger safari, Betla Fort ruins, dense forests.", "entry_fee": "₹50 – 200", "travel_cost_estimate": "800 – 2500", "best_time_visit": "Nov–March | Sunrise – Sunset"},
#         {"name": "Topchanchi Wildlife Sanctuary", "description": "Sanctuary around Topchanchi Lake, home to migratory birds and wildlife.", "historical_background": "Lake built during British era for water supply.", "scenic_spots": "Topchanchi Lake, forest trails, birdwatching.", "entry_fee": "₹20 – 50", "travel_cost_estimate": "400 – 1500", "best_time_visit": "Oct–Feb (bird season) | Sunrise – Sunset"},
#         {"name": "Netarhat", "description": "Queen of Chotanagpur plateau known for pine forests and sunrise/sunset points.", "historical_background": "Developed during the British period as a hill station; home to the renowned Netarhat Residential School (est. 1954).", "scenic_spots": "Sunrise Point, Magnolia Sunset Point, Pine forests, Koel View Point, Upper/Lower Ghaghri Falls (nearby).", "nearby_restaurants_hotels": "Netarhat Tourist Lodge, Prabhat Vihar, local dhabas", "entry_fee": "₹30 – 50 (viewpoints)", "food_cost_range": "150 – 400", "travel_cost_estimate": "800 – 2200", "stay_cost_per_night": "800 – 2000", "best_time_visit": "Oct–March; also Monsoon for waterfalls | All day"},
#         {"name": "Patratu Valley", "description": "Scenic valley roads with sweeping hairpin bends and reservoir views near Ranchi.", "historical_background": "Valley developed around the Patratu Dam (constructed in the 1960s) supporting the Patratu Thermal Power Station.", "scenic_spots": "Patratu Dam & Reservoir, valley viewpoints, serpentine ghat roads, lakeside promenade.", "nearby_restaurants_hotels": "Patratu Lake Resort, lakeside cafes, local eateries", "entry_fee": "₹25 – 50 (promenade/parking)", "food_cost_range": "120 – 350", "travel_cost_estimate": "500 – 1500", "stay_cost_per_night": "1200 – 2500", "best_time_visit": "Oct–Feb (clear views); evenings for sunset | Sunrise – Sunset"},
#         {"name": "Hazaribagh Lake", "description": "Serene urban lake with walking paths; gateway to Hazaribagh National Park.", "historical_background": "Constructed during the British era as a series of interconnected artificial lakes in Hazaribagh town.", "scenic_spots": "Lakeside promenade, boating area, viewpoints; national park and Canary Hill nearby.", "nearby_restaurants_hotels": "Local eateries around Lake Road, town hotels and lodges", "entry_fee": "₹10 – 20", "food_cost_range": "120 – 300", "travel_cost_estimate": "400 – 1200", "stay_cost_per_night": "700 – 1500", "best_time_visit": "Oct–Feb (pleasant weather); evenings for sunset | 6:00 AM – 8:00 PM"},
#     ]
#     with Session(engine) as session:
#         if not session.exec(select(Attraction)).first():
#             print("Seeding attractions data...")
#             for item in sample:
#                 session.add(Attraction(**item))
#             session.commit()
#             print("Seeding complete.")
#         else:
#             print("Attractions data already exists.")

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("Creating tables...")
#     SQLModel.metadata.create_all(engine)
#     seed_data()
#     yield
#     print("Shutting down...")


# app = FastAPI(lifespan=lifespan)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Razorpay client
# razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# @app.get("/")
# def root():
#     return {"message": "Server is running"}


# @app.post("/create_order")
# async def create_order(tourist_name: str = Form(...), email: str = Form(...), package: str = Form(...), amount: float = Form(...), db: Session = Depends(get_session)):
#     if not RAZORPAY_KEY_ID or RAZORPAY_KEY_ID == "your_key_id":
#         raise HTTPException(status_code=500, detail="Razorpay keys not configured on the server.")
#     amount_paise = int(amount * 100)
#     try:
#         order = razorpay_client.order.create({"amount": amount_paise, "currency": "INR", "payment_capture": 1})
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Razorpay error: {e}")

#     booking = TouristBooking(tourist_name=tourist_name, email=email, package=package, amount=amount, order_id=order["id"])
#     db.add(booking)
#     db.commit()
#     db.refresh(booking)
#     return {"order_id": order["id"], "amount": amount_paise, "currency": "INR", "key": RAZORPAY_KEY_ID, "booking_id": booking.id, "prefill": {"name": tourist_name, "email": email}}


# @app.post("/verify_payment")
# async def verify_payment(request: Request, db: Session = Depends(get_session)):
#     data = await request.json()
#     razorpay_order_id = data.get("razorpay_order_id")
#     razorpay_payment_id = data.get("razorpay_payment_id")
#     razorpay_signature = data.get("razorpay_signature")
#     if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
#         raise HTTPException(status_code=400, detail="Missing Razorpay payment details.")
#     try:
#         razorpay_client.utility.verify_payment_signature({'razorpay_order_id': razorpay_order_id, 'razorpay_payment_id': razorpay_payment_id, 'razorpay_signature': razorpay_signature})
#     except razorpay.errors.SignatureVerificationError:
#         raise HTTPException(status_code=400, detail="Payment verification failed: Invalid signature.")
#     booking = db.exec(select(TouristBooking).where(TouristBooking.order_id == razorpay_order_id)).first()
#     if not booking:
#         raise HTTPException(status_code=404, detail="Booking not found for this order.")
#     booking.payment_id = razorpay_payment_id
#     booking.status = "PAID"
#     db.add(booking)
#     db.commit()
#     return {"status": "success", "message": "Payment verified successfully", "order_id": razorpay_order_id}


# @app.get("/attractions", response_model=List[AttractionRead])
# def get_attractions(q: Optional[str] = Query(None, description="Search attractions"), db: Session = Depends(get_session)):
#     statement = select(Attraction)
#     if q:
#         statement = statement.where(or_(Attraction.name.contains(q), Attraction.description.contains(q)))
#     return db.exec(statement).all()


# @app.get("/attractions/{attraction_id}", response_model=AttractionRead)
# def get_attraction(attraction_id: int, db: Session = Depends(get_session)):
#     attraction = db.get(Attraction, attraction_id)
#     if not attraction:
#         raise HTTPException(status_code=404, detail="Attraction not found")
#     return attraction


# @app.get("/destinations")
# def get_destinations():
#     return {"destinations": [{"id": 1, "name": "Ranchi"}, {"id": 2, "name": "Jamshedpur"}, {"id": 3, "name": "Dhanbad"}, {"id": 4, "name": "Hazaribagh"}]}


# @app.post("/attractions", response_model=AttractionRead)
# def create_attraction(attraction: AttractionCreate, db: Session = Depends(get_session)):
#     db_attraction = Attraction.from_orm(attraction)
#     db.add(db_attraction)
#     db.commit()
#     db.refresh(db_attraction)
#     return db_attraction


# @app.put("/attractions/{attraction_id}", response_model=AttractionRead)
# def update_attraction(attraction_id: int, data: AttractionUpdate, db: Session = Depends(get_session)):
#     db_attraction = db.get(Attraction, attraction_id)
#     if not db_attraction:
#         raise HTTPException(status_code=404, detail="Attraction not found")
#     update_data = data.dict(exclude_unset=True)
#     for key, value in update_data.items():
#         setattr(db_attraction, key, value)
#     db.add(db_attraction)
#     db.commit()
#     db.refresh(db_attraction)
#     return db_attraction


# @app.delete("/attractions/{attraction_id}")
# def delete_attraction(attraction_id: int, db: Session = Depends(get_session)):
#     attraction = db.get(Attraction, attraction_id)
#     if not attraction:
#         raise HTTPException(status_code=404, detail="Attraction not found")
#     db.delete(attraction)
#     db.commit()
#     return {"ok": True}
from tethysext.hydroviewer.model import HydroviewerExtensionBase

from sqlalchemy.orm import sessionmaker

def init_catalog_db(engine, first_time):
    """
    Initializer for the primary database.
    """
    # Create all the tables
    if first_time:
        HydroviewerExtensionBase.metadata.create_all(engine)
        # # Make session
        SessionMaker = sessionmaker(bind=engine)
        session = SessionMaker()
        session.close()
        print("Finishing Initializing Persistent Storage")
    
    else:
        print("Persistent Storage Already Initialized")
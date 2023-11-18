import pdb
from notice.models import Notice
from appuser.models import AdaptorUser as User
from repair.models import Repair
from parking.models import ParkingRequest


def notice(request):
    notice = parkingnum =  repairnum = 0

    if request:
        if request.user:
            user = request.user
            if not request.user.is_anonymous:
                if request.user.organize:
                    notices = Notice.objects.filter(org = request.user.organize, read=Notice.UNREAD)
                    notice = len(notices)
                    repairnum = Repair.objects.filter(property__building__org=user.organize,
                                                      status=Repair.ONGOING,
                                                      org_delete=0).count()
                    parkingnum = ParkingRequest.objects.filter(parkingmgr__org=user.organize,
                                                               status=ParkingRequest.ONGOING,
                                                               org_delete=0).count()

    return {"notice":notice, 'requestsnum': parkingnum + repairnum}
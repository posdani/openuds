# -*- coding: utf-8 -*-

#
# Copyright (c) 2012-2020 Virtual Cable S.L.U.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#    * Neither the name of Virtual Cable S.L. nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
.. moduleauthor:: Adolfo Gómez, dkmaster at dkmon dot com
"""
import datetime
import logging
import typing
import types

from django.db import models

from .util import NEVER_UNIX
from .util import getSqlDatetimeAsUnix

logger = logging.getLogger(__name__)


class StatsEvents(models.Model):
    """
    Statistics about events (login, logout, whatever...)
    """

    owner_id = models.IntegerField(db_index=True, default=0)
    owner_type = models.SmallIntegerField(db_index=True, default=0)
    event_type = models.SmallIntegerField(db_index=True, default=0)
    stamp = models.IntegerField(db_index=True, default=0)

    # Variable fields, depends on event
    fld1 = models.CharField(max_length=128, default='')
    fld2 = models.CharField(max_length=128, default='')
    fld3 = models.CharField(max_length=128, default='')
    fld4 = models.CharField(max_length=128, default='')

    # "fake" declarations for type checking
    objects: 'models.manager.Manager[StatsEvents]'

    class Meta:
        """
        Meta class to declare db table
        """

        db_table = 'uds_stats_e'
        app_label = 'uds'

    @staticmethod
    def get_stats(
        owner_type: typing.Union[int, typing.Iterable[int]],
        event_type: typing.Union[int, typing.Iterable[int]],
        **kwargs,
    ) -> 'models.QuerySet[StatsEvents]':
        """
        Returns a queryset with the average stats grouped by interval for owner_type and owner_id (optional)

        Note: if someone cant get this more optimized, please, contribute it!
        """
        if isinstance(event_type, (list, tuple, types.GeneratorType)):
            fltr = StatsEvents.objects.filter(event_type__in=event_type)
        else:
            fltr = StatsEvents.objects.filter(event_type=event_type)

        if isinstance(owner_type, (list, tuple, types.GeneratorType)):
            fltr = fltr.filter(owner_type__in=owner_type)
        else:
            fltr = fltr.filter(owner_type=owner_type)

        if kwargs.get('owner_id', None) is not None:
            oid = kwargs.get('owner_id')
            if isinstance(oid, (list, tuple)):
                fltr = fltr.filter(owner_id__in=oid)
            else:
                fltr = fltr.filter(owner_id=oid)

        since = kwargs.get('since', None)
        to = kwargs.get('to', None)

        since = int(since) if since else NEVER_UNIX
        to = int(to) if to else getSqlDatetimeAsUnix()

        fltr = fltr.filter(stamp__gte=since, stamp__lt=to)

        # We use result as an iterator
        return fltr

    # Utility aliases for reading
    @property
    def username(self) -> str:
        return self.fld1

    @property
    def srcIp(self) -> str:
        return self.fld2

    @property
    def dstIp(self) -> str:
        return self.fld3

    @property
    def uniqueId(self) -> str:
        return self.fld4

    @property
    def isostamp(self) -> str:
        """
        Returns the timestamp in ISO format (UTC)
        """
        stamp = datetime.datetime.utcfromtimestamp(self.stamp)
        return stamp.isoformat()

    # returns CSV header
    @staticmethod
    def getCSVHeader(
        sep: str = '',
    ) -> str:
        return sep.join(
            [
                'owner_type',
                'owner_id',
                'event_type',
                'stamp',
                'field_1',
                'field_2',
                'field_3',
                'field_4',
            ]
        )

    # Return record as csv line using separator (default: ',')
    def toCsv(self, sep: str = ',') -> str:
        from uds.core.util.stats.events import EVENT_NAMES, TYPES_NAMES

        return sep.join(
            [
                TYPES_NAMES.get(self.owner_type, '?'),
                str(self.owner_id),
                EVENT_NAMES.get(self.event_type, '?'),
                str(self.isostamp),
                self.fld1,
                self.fld2,
                self.fld3,
                self.fld4,
            ]
        )

    def __str__(self):
        return 'Log of {}({}): {} - {} - {}, {}, {}'.format(
            self.owner_type,
            self.owner_id,
            self.event_type,
            self.stamp,
            self.fld1,
            self.fld2,
            self.fld3,
        )

# -*- coding: utf-8 -*-
"""



"""

from .baserawio import (BaseRawIO, _signal_channel_dtype, _unit_channel_dtype, 
        _event_channel_dtype)

import numpy as np

class ExampleRawIO(BaseRawIO):
    """
    Class for "reading" fake data from an imaginary file.

    For the user, it give acces to raw data (signals, event, spikes) as they
    are in the file (imaginary) int16 and int64.

    For a developer, it is just an example showing guidelines for someone who wants
    to develop a new IO module.
    
    Two rules for developers:
      * Respect the Neo IO API (:ref:`neo_io_API`)
      * Follow :ref:`io_guiline`

    This fake IO:
        * have 2 blocks
        * blocks have 2 and 3 segments
        * have 16 signal_channel sample_rate = 10000
        * have 3 unit_channel
        * have 2 event channel: one have *type=event*, the other have
          *type=epoch*
    

    Usage:
        >>> import neo.rawio
        >>> r = neo.rawio.ExampleRawIO(filename='itisafake.nof')
        >>> r.parse_header()
        >>> print(r)
        >>> raw_chunk = r.get_analogsignal_chunk(block_index=0, seg_index=0,
                            i_start=0, i_stop=1024,  channel_names=channel_names)
        >>> float_chunk = reader.rescale_signal_raw_to_float(raw_chunk, dtype='float64', 
                            channel_indexes=[0, 3, 6])
        >>> spike_timestamp = reader.spike_timestamps(unit_index=0, t_start=None, t_stop=None)
        >>> spike_times = reader.rescale_spike_timestamp(spike_timestamp, 'float64')
        >>> ev_timestamps, _, ev_labels = reader.event_timestamps(event_channel_index=0)
    
    """
    def __init__(self, filename=''):
        BaseRawIO.__init__(self)
        #note that this filename is ued in self._source_name
        self.filename = filename 
    
    def _parse_header(self):
        #make channels
        sig_channels = []
        for c in range(16):
            sig_channels.append(('ch{}'.format(c), 'id#{}'.format(c), 'uV', 1000./2**16, 0.))
        sig_channels = np.array(sig_channels, dtype=_signal_channel_dtype)
        
        unit_channels = []
        for c in range(3):
            unit_channels.append(('unit{}'.format(c), '#{}'.format(c), 'uV', 1000./2**16, 0.))
        unit_channels = np.array(unit_channels, dtype=_unit_channel_dtype)
        
        event_channels = []
        event_channels.append(('Some events', 'ev_0', 'event'))
        event_channels.append(('Some epochs', 'ep_1', 'epoch'))
        event_channels = np.array(event_channels, dtype=_event_channel_dtype)
        
        #fille into header dict
        self.header = {}
        self.header['nb_block'] = 2
        self.header['nb_segment'] = [2, 3]
        self.header['signal_channels'] = sig_channels
        self.header['unit_channels'] = unit_channels
        self.header['event_channels'] = event_channels
    
    def _source_name(self):
        return self.filename
    
    def _block_count(self):
        return self.header['nb_block']
    
    def _segment_count(self, block_index):
        assert 0<=block_index<2, "I don't like your jokes"
        return self.header['nb_segment'][block_index]
    
    def _segment_t_start(self, block_index, seg_index):
        # always in second
        all_starts = [[0., 15.], [0., 20., 60.]]
        return all_starts[block_index][seg_index]
    
    def _analogsignal_shape(self, block_index, seg_index):
        # we are lucky: signals in all segment have the same shape!! (10.24 seconds)
        # it is not always the case
        return (102400, 16)

    def _get_analogsignal_chunk(self, block_index, seg_index,  i_start, i_stop, channel_indexes):
        #we are lucky:  our signals is always zeros!!
        #it is not always the case
        #internally signals are int16 
        #convertion to real units is done with self.header['signal_channels']
        
        if i_start is None: i_start=0
        if i_stop is None: i_stop=102400
        
        assert i_start>=0, "I don't like your jokes"
        assert i_stop<=102400, "I don't like your jokes"
        
        raw_signals = np.zeros((i_stop-i_start, len(channel_indexes)), dtype='int16')
        return raw_signals
    
    def analogsignal_sampling_rate(self):
        # always float in Hz
        return 10000. #Hz
    
    def _spike_count(self,  block_index, seg_index, unit_index):
        #we are lucky:  our units have all the same nb of spikes!!
        #it is not always the case
        nb_spikes = 20
        return nb_spikes
    
    def _spike_timestamps(self,  block_index, seg_index, unit_index, t_start, t_stop):
        # In our IO, timstamp are internally coded 'int64' and they
        # represent the index of the signals 10kHz
        # we are lucky: spikes have the same discharge in all segments!!
        # incredible!! in is not always the case
        spike_timestamps = np.arange(0, 10000, 500)
        
        if t_start is not None or t_stop is not None:
            #restricte spikes to given limits (in seconds)
            lim0 = int(t_start*10000)
            lim1 = int(t_stop*10000)
            mask = (spike_timestamps>=lim0) & (spike_timestamps<=lim1)
            spike_timestamps = spike_timestamps[mask]
        
        return spike_timestamps
    
    def _rescale_spike_timestamp(self, spike_timestamps, dtype):
        spike_times = spike_timestamps.astype(dtype)
        spike_times /= 10000. # because 10kHz
        return spike_times

    def _spike_raw_waveforms(self, block_index, seg_index, unit_index, t_start, t_stop):
        #In our IO waveforms come from all channels
        #they are int16
        #convertion to real units is done with self.header['unit_channels']
        #here a realistic case all waveforms are only noise.
        #it is not always the case
        # we 20 spikes with a sweep of 50 (5ms)
        
        np.random.seed(2205) # a magic number (my birthday)
        waveforms = np.random.randint(low=-2**4, high=2**4, size=20*50, dtype='int16')
        waveforms = waveforms.reshape(20, 1, 50)
        return waveforms
    
    def _event_count(self, block_index, seg_index, event_channel_index):
        # we have 2 event channels
        if event_channel_index==0:
            #event channel
            return 6
        elif event_channel_index==1:
            #epoch channel
            return 10
    
    def _event_timestamps(self,  block_index, seg_index, event_channel_index, t_start, t_stop):
        # in our IO event are directly coded in seconds
        if event_channel_index==0:
            timestamp = np.arange(0, 6, dtype='float64')
            durations = None
            labels = np.array(['trigger_a', 'trigger_b']*3, dtype='U12')
        elif event_channel_index==1:
            timestamp = np.arange(0, 10, dtype='float64') + .5
            durations = np.ones((10),  dtype='float64') * .25
            labels = np.array(['zoneX']*5+['zoneZ']*5, dtype='U12')
        
        return timestamp, durations, labels

    
    def _rescale_event_timestamp(self, event_timestamps, dtype):
        # really easy here because in our case it is already seconds
        event_times = event_timestamps.astype(dtype)
        return event_times


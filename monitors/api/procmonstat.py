"""
Process monitor statistics object.

@author Xiangyu Bu <bu1@purdue.edu>
"""

# Python2 statistics module placed under /scripts/libs/statistics.
import statistics


class ProcMonStatAlg:
    MEAN = 0
    MAX = 1


class ProcMonStat:

    # Token strings used in the C process of procmon.
    STAT_BEGIN_TOKEN = '# STAT_BEGIN'
    STAT_END_TOKEN = '# STAT END'

    # Description for each stat field.
    FIELD_DESC = {
        'cpu_sec': 'Total CPU time (sec)',
        'total_sec': 'Total exec time (sec)',
        'avg_cpu_percent': 'Average CPU usage (percent)',
        'peak_cpu_percent': 'Peak CPU usage (percent)',
        'avg_rss_size_kib': 'Average RAM usage (KiB)',
        'peak_rss_size_kib': 'Peak RAM usage (KiB)'
    }

    # Raise alarm if [new value] / [base value] > [multiplier].
    DEFAULT_MULTIPLIERS = {
        'cpu_sec': 2.0,
        # Omit fields that we don't care.
        # 'total_sec': 2,
        # 'avg_cpu_percent': 1,
        # 'peak_cpu_percent': 1,
        'avg_rss_size_kib': 2.0,
        'peak_rss_size_kib': 3.0
    }

    # Default threshold for rebaselining. +/- 5% of failure threshold value.
    DEFAULT_REBASE_THRESHOLD = 0.05

    def __init__(self, multipliers=DEFAULT_MULTIPLIERS, alg='max', rebase_threshold=DEFAULT_REBASE_THRESHOLD):
        """
        Initialize object with baseline data and multiplier.
        :param dict[str, float] multipliers: Raise threshold when stat KEY is VALUE times baseline.
        :param str alg: Algorithm for baselining. Either 'max' or 'mean'.
        :param float rebase_threshold:
        """
        self.multipliers = multipliers
        self.base_stat = dict()
        self.base_ready = False
        self.rebase_threshold = rebase_threshold
        self._alg = ProcMonStatAlg.MEAN if alg == 'mean' else ProcMonStatAlg.MAX
        self._base_history = {k: [] for k in multipliers}
        print 'Stat created: {alg=%s, multipliers=%s, rebase=%f}' % ('mean' if alg == 'mean' else 'max', str(multipliers), rebase_threshold)

    def add_baseline(self, stat_dict):
        """
        Add a new stat dict to baseline set.
        :param dict[str, float] stat_dict: A stat dict generated by perfmon.
        """
        if not isinstance(stat_dict, dict):
            raise ValueError('Stat baseline must be a stat dict.')
        for k in self.multipliers:  # Only save numbers that matter.
            try:
                self._base_history[k].append(stat_dict[k])
            except KeyError as e:
                raise ValueError('Failed to add baseline: key ' + str(e) + ' is missing.')

    def calc_baseline(self):
        """
        Calculate the baseline thresholds given all baseline stat recorded.
        """
        if self._alg == ProcMonStatAlg.MAX:
            for k in self.multipliers:
                self.base_stat[k] = max(self._base_history[k])
        else:
            for k in self.multipliers:
                avg = statistics.mean(self._base_history[k])
                dev = statistics.stdev(self._base_history[k])
                self.base_stat[k] = avg + dev + dev
        for k in self._base_history:
            self._base_history[k] = []   # Clear baseline history.
        self.base_ready = True

    def test_stat(self, stat_dict=None, stdout=None):
        """
        Test newly generated statistical data against baseline and multiplier.
        """
        if stdout is not None:
            stat_dict = self.extract_stat(stdout)
        errors = []
        suggest_rebase = 0

        for k in self.multipliers:
            if k not in stat_dict or k not in self.base_stat:
                continue
            # print k, self.multipliers[k]
            mx = stat_dict[k] / self.base_stat[k]
            # print mx
            if mx > self.multipliers[k]:
                errors.append('%s is %.3f%% of baseline' % (self.FIELD_DESC[k], mx * 100))
            if abs(mx - self.multipliers[k]) <= self.rebase_threshold:
                suggest_rebase += 1

        return len(errors) == 0, errors, suggest_rebase

    @classmethod
    def extract_stat(cls, stdout):
        """
        Extract the statistical data from procmon stdout and return a
        Python dict type.
        """
        if isinstance(stdout, str):
            # Read from string.
            first_split = stdout.split(cls.STAT_BEGIN_TOKEN, 1)
            if len(first_split) != 2:
                raise ValueError('Stat begin token not found.')
            stdout = first_split[1]
            code = stdout.split(cls.STAT_END_TOKEN, 1)[0]
        else:
            # Read from large file-like object.
            for line in stdout:
                if line.startswith(cls.STAT_BEGIN_TOKEN):
                    break
            code = ''
            for line in stdout:
                if line.startswith(cls.STAT_END_TOKEN):
                    break
                code += line
        if len(code) == 0:
            raise ValueError('No statistical data found.')
        return eval(code)

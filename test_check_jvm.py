# -*- coding: utf-8 -*-

# ----------------------------------------------
# test_check_jvm.py
#
# Copyright(C) 2014 Yuichiro SAITO
# This software is released under the MIT License, see LICENSE.txt.
# ----------------------------------------------

import unittest
import os
import logging
import copy
from check_jvm import _Jvm


# ----------------------------------------------

class TestSequenceFunctions(unittest.TestCase):

    # ----------------------------------------------

    def setUp(self):
        self.baseJstatData = {
            "E": 59.0, 
            "YGCT": 10.0, 
            "Timestamp": 1800, 
            "S1": 52.0, 
            "S0": 0.0, 
            "pid": 16276, 
            "FGCT": 500.0, 
            "O": 90, 
            "P": 68, 
            "GCT": 10.0, 
            "YGC": 655.0, 
            "FGC": 10.0
        }
        self.java_bin = "/usr/java/jdk1.7.0_72/bin"
        self.temp_dir = "/tmp"
        self.name = "test"
        self.interval = 100
        self.history1_filename = "%s/%s" % (self.temp_dir, _Jvm.TEMPFILE_NAME % 1)
        self.history2_filename = "%s/%s" % (self.temp_dir, _Jvm.TEMPFILE_NAME % 2)

    # ----------------------------------------------

    def _clearJstatLog(self):

        if os.path.exists(self.history1_filename):
            os.remove(self.history1_filename)
        if os.path.exists(self.history2_filename):
            os.remove(self.history2_filename)

    # ----------------------------------------------

    def _initJstatLog(self, checker):

        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data1 = copy.deepcopy(self.baseJstatData)
        save_data1["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval
        save_data1["FGC"] = 5.0
        save_data1["FGCT"] = 300.0
        checker._saveJson(self.history1_filename, save_data1)

        save_data2 = copy.deepcopy(self.baseJstatData)
        save_data2["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2
        checker._saveJson(self.history2_filename, save_data2)
        
        checker.old_stat = checker._getOldStat()

    # ----------------------------------------------

    def test_paramCheckGC_1(self):
        """
        GC時間 Critical
        """
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        self._initJstatLog(checker)
        checker.setTimeWarning(199)
        checker.setTimeCritical(200)
        checker.setCountWarning(11)
        checker.setCountCritical(12)
        self.assertEqual(checker.checkGc(), _Jvm.STATE_CRITICAL)

    # ----------------------------------------------

    def test_paramCheckGC_2(self):
        """
        GC時間 Warning
        """
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        self._initJstatLog(checker)
        checker.setTimeWarning(200)
        checker.setTimeCritical(201)
        checker.setCountWarning(11)
        checker.setCountCritical(12)
        self.assertEqual(checker.checkGc(), _Jvm.STATE_WARNING)

    # ----------------------------------------------

    def test_paramCheckGC_3(self):
        """
        GC回数 Critical
        """
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        self._initJstatLog(checker)
        checker.setTimeWarning(301)
        checker.setTimeCritical(302)
        checker.setCountWarning(4)
        checker.setCountCritical(5)
        self.assertEqual(checker.checkGc(), _Jvm.STATE_CRITICAL)

    # ----------------------------------------------

    def test_paramCheckGC_4(self):
        """
        GC時間 Warning
        """
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        self._initJstatLog(checker)
        checker.setTimeWarning(301)
        checker.setTimeCritical(302)
        checker.setCountWarning(5)
        checker.setCountCritical(6)
        self.assertEqual(checker.checkGc(), _Jvm.STATE_WARNING)

    # ----------------------------------------------

    def test_paramCheck_OK_1(self):
        """
        矛盾しないチェック time
        """
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        ret = checker.setTimeWarning(10)
        ret = checker.setTimeCritical(20)
        self.assertEqual(ret, _Jvm.STATE_OK)

    # ----------------------------------------------

    def test_paramCheck_OK_2(self):
        """
        矛盾しないチェック count
        """
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        ret = checker.setCountWarning(10)
        ret = checker.setCountCritical(20)
        self.assertEqual(ret, _Jvm.STATE_OK)

    # ----------------------------------------------

    def test_paramCheck_Unknown_1(self):
        """
        矛盾チェック time
        """
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        ret = checker.setTimeWarning(20)
        ret = checker.setTimeCritical(10)
        self.assertEqual(ret, _Jvm.STATE_UNKNOWN)

    # ----------------------------------------------

    def test_paramCheck_Unknown_2(self):
        """
        矛盾チェック count
        """
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        ret = checker.setCountWarning(20)
        ret = checker.setCountCritical(10)
        self.assertEqual(ret, _Jvm.STATE_UNKNOWN)

    # ----------------------------------------------
    
    def test_parseGcUtil_1(self):
        """
        パーサーチェック
        """

        data = """Timestamp         S0     S1     E      O      P     YGC     YGCT    FGC    FGCT     GCT   
18276.7  78.11   0.00  68.34  61.65  60.03   2342   33.595    16    0.166   33.762"""
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        ret = checker._parseGcUtil(data)
        self.assertEqual(ret["S1"], 0)
        self.assertEqual(ret["GCT"], 33.762)

    # ----------------------------------------------
    
    def test_getOldStat_1(self):
        """
        過去データ取得: 初期状態
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        ret = checker._getOldStat()
        self.assertEqual(ret, None)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history1_filename)
        self.assertEqual(history1, self.baseJstatData)
        self.assertEqual(history2, self.baseJstatData)

    # ----------------------------------------------
    
    def test_getOldStat_2(self):
        """
        過去データ取得: 計測開始時間直前
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data = copy.deepcopy(self.baseJstatData)
        save_data["Timestamp"] = save_data["Timestamp"] - self.interval + 1
        checker._saveJson(self.history1_filename, save_data)
        checker._saveJson(self.history2_filename, save_data)

        ret = checker._getOldStat()
        self.assertEqual(ret, None)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, save_data)
        self.assertEqual(history2, save_data)

    # ----------------------------------------------
    
    def test_getOldStat_3(self):
        """
        過去データ取得: 1回目計測開始時間
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data = copy.deepcopy(self.baseJstatData)
        save_data["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval
        checker._saveJson(self.history1_filename, save_data)
        checker._saveJson(self.history2_filename, save_data)

        ret = checker._getOldStat()
        self.assertEqual(ret, save_data)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, save_data)
        self.assertEqual(history2, self.baseJstatData)

    # ----------------------------------------------
    
    def test_getOldStat_4(self):
        """
        過去データ取得: 1回目計測終了時間
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data = copy.deepcopy(self.baseJstatData)
        save_data["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2 + 1
        checker._saveJson(self.history1_filename, save_data)
        checker._saveJson(self.history2_filename, save_data)

        ret = checker._getOldStat()
        self.assertEqual(ret, save_data)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, save_data)
        self.assertEqual(history2, self.baseJstatData)

    # ----------------------------------------------
    
    def test_getOldStat_5(self):
        """
        過去データ取得: 1回目計測終了時間 2回目取得完了
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data1 = copy.deepcopy(self.baseJstatData)
        save_data1["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2 + 1
        checker._saveJson(self.history1_filename, save_data1)

        save_data2 = copy.deepcopy(self.baseJstatData)
        save_data2["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval + 1
        checker._saveJson(self.history2_filename, save_data2)

        ret = checker._getOldStat()
        self.assertEqual(ret, save_data1)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, save_data1)
        self.assertEqual(history2, save_data2)

    # ----------------------------------------------
    
    def test_getOldStat_6(self):
        """
        過去データ取得: 2回目計測開始時間
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data1 = copy.deepcopy(self.baseJstatData)
        save_data1["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2
        checker._saveJson(self.history1_filename, save_data1)

        save_data2 = copy.deepcopy(self.baseJstatData)
        save_data2["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval
        checker._saveJson(self.history2_filename, save_data2)

        ret = checker._getOldStat()
        self.assertEqual(ret, save_data2)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, self.baseJstatData)
        self.assertEqual(history2, save_data2)

    # ----------------------------------------------
    
    def test_getOldStat_7(self):
        """
        過去データ取得: 2回目計測終了時間
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data1 = copy.deepcopy(self.baseJstatData)
        save_data1["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 3 + 1
        checker._saveJson(self.history1_filename, save_data1)

        save_data2 = copy.deepcopy(self.baseJstatData)
        save_data2["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2 + 1
        checker._saveJson(self.history2_filename, save_data2)

        ret = checker._getOldStat()
        self.assertEqual(ret, save_data2)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, self.baseJstatData)
        self.assertEqual(history2, save_data2)

    # ----------------------------------------------
    
    def test_getOldStat_8(self):
        """
        過去データ取得: 2回目計測終了時間 3回目取得完了
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data1 = copy.deepcopy(self.baseJstatData)
        save_data1["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval + 1
        checker._saveJson(self.history1_filename, save_data1)

        save_data2 = copy.deepcopy(self.baseJstatData)
        save_data2["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2 + 1
        checker._saveJson(self.history2_filename, save_data2)

        ret = checker._getOldStat()
        self.assertEqual(ret, save_data2)

        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, save_data1)
        self.assertEqual(history2, save_data2)

    # ----------------------------------------------
    
    def test_getOldStat_9(self):
        """
        過去データ取得: 3回目計測開始時間
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data1 = copy.deepcopy(self.baseJstatData)
        save_data1["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval
        checker._saveJson(self.history1_filename, save_data1)

        save_data2 = copy.deepcopy(self.baseJstatData)
        save_data2["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2
        checker._saveJson(self.history2_filename, save_data2)

        ret = checker._getOldStat()
        self.assertEqual(ret, save_data1)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, save_data1)
        self.assertEqual(history2, self.baseJstatData)

    # ----------------------------------------------
    
    def test_getOldStat_A(self):
        """
        過去データ取得: データ古過ぎ
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data1 = copy.deepcopy(self.baseJstatData)
        save_data1["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2
        checker._saveJson(self.history1_filename, save_data1)

        save_data2 = copy.deepcopy(self.baseJstatData)
        save_data2["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 3
        checker._saveJson(self.history2_filename, save_data2)

        ret = checker._getOldStat()
        self.assertEqual(ret, None)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, self.baseJstatData)
        self.assertEqual(history2, self.baseJstatData)

    # ----------------------------------------------
    
    def test_getOldStat_B(self):
        """
        過去データ取得: データ古過ぎ パターン2
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data1 = copy.deepcopy(self.baseJstatData)
        save_data1["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 3
        checker._saveJson(self.history1_filename, save_data1)

        save_data2 = copy.deepcopy(self.baseJstatData)
        save_data2["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2
        checker._saveJson(self.history2_filename, save_data2)

        ret = checker._getOldStat()
        self.assertEqual(ret, None)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, self.baseJstatData)
        self.assertEqual(history2, self.baseJstatData)

    # ----------------------------------------------
    
    def test_getOldStat_C(self):
        """
        過去データ取得: 片方だけ データ古過ぎ
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data1 = copy.deepcopy(self.baseJstatData)
        save_data1["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 1
        checker._saveJson(self.history1_filename, save_data1)

        save_data2 = copy.deepcopy(self.baseJstatData)
        save_data2["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2
        checker._saveJson(self.history2_filename, save_data2)

        ret = checker._getOldStat()
        self.assertEqual(ret, save_data1)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, save_data1)
        self.assertEqual(history2, self.baseJstatData)

    # ----------------------------------------------
    
    def test_getOldStat_D(self):
        """
        過去データ取得: 片方だけ データ古過ぎ 逆パターン
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data1 = copy.deepcopy(self.baseJstatData)
        save_data1["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2
        checker._saveJson(self.history1_filename, save_data1)

        save_data2 = copy.deepcopy(self.baseJstatData)
        save_data2["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 1
        checker._saveJson(self.history2_filename, save_data2)

        ret = checker._getOldStat()
        self.assertEqual(ret, save_data2)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, self.baseJstatData)
        self.assertEqual(history2, save_data2)

    # ----------------------------------------------
    
    def test_getOldStat_E(self):
        """
        過去データ取得: データ古過ぎ＆データ新し過ぎ
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data1 = copy.deepcopy(self.baseJstatData)
        save_data1["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval + 1
        checker._saveJson(self.history1_filename, save_data1)

        save_data2 = copy.deepcopy(self.baseJstatData)
        save_data2["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2
        checker._saveJson(self.history2_filename, save_data2)

        ret = checker._getOldStat()
        self.assertEqual(ret, None)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, save_data1)
        self.assertEqual(history2, save_data2)

    # ----------------------------------------------
    
    def test_getOldStat_F(self):
        """
        過去データ取得: データ古過ぎ＆データ新し過ぎ 逆パターン
        """
        self._clearJstatLog()
        checker = _Jvm(self.java_bin, self.temp_dir, self.name, self.interval)
        checker.current_stat = self.baseJstatData
        checker.pid = self.baseJstatData["pid"]

        save_data1 = copy.deepcopy(self.baseJstatData)
        save_data1["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval * 2
        checker._saveJson(self.history1_filename, save_data1)

        save_data2 = copy.deepcopy(self.baseJstatData)
        save_data2["Timestamp"] = self.baseJstatData["Timestamp"] - self.interval + 1
        checker._saveJson(self.history2_filename, save_data2)

        ret = checker._getOldStat()
        self.assertEqual(ret, None)
        
        history1 = checker._loadJson(self.history1_filename)
        history2 = checker._loadJson(self.history2_filename)
        self.assertEqual(history1, save_data1)
        self.assertEqual(history2, save_data2)

# ----------------------------------------------

if __name__ == '__main__':
    logging.basicConfig(level=logging.CRITICAL, format='%(levelname)s\t%(asctime)s\t%(name)s\t%(funcName)s\t"%(message)s"')
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSequenceFunctions)
    unittest.TextTestRunner(verbosity=2).run(suite)

# ----------------------------------------------

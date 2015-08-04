# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

from nose.plugins.attrib import attr

import hgvs.dataproviders.uta
import hgvs.parser
import hgvs.variantmapper


@attr(tags=["quick"])
class Test_VariantMapper(unittest.TestCase):
    def setUp(self):
        self.hdp = hgvs.dataproviders.uta.connect()
        self.vm = hgvs.variantmapper.VariantMapper(self.hdp)
        self.hp = hgvs.parser.Parser()

    def test_VariantMapper_quick(self):
        # From garcia.tsv:
        hgvs_g = 'NC_000007.13:g.36561662C>T'
        hgvs_c = 'NM_001637.3:c.1582G>A'
        hgvs_p = 'NP_001628.1:p.(Gly528Arg)'    # from Mutalyzer

        var_g = self.hp.parse_hgvs_variant(hgvs_g)
        var_c = self.vm.g_to_c(var_g, 'NM_001637.3')
        var_p = self.vm.c_to_p(var_c)

        self.assertEqual(str(var_c), hgvs_c)
        self.assertEqual(str(var_p), hgvs_p)
    
    def test_VariantMapper_for_complex_variants(self):
        compound_c = 'NM_000495.4:c.[1117C>T;4994_5001del]'
        mosaic_c   = 'NM_000495.4:c.[=/1117C>T]'
        chimeric_c = 'NM_000495.4:c.[=//1117C>T]'
        
        var_compound_c = self.hp.parse_hgvs_variant(compound_c)
        var_mosaic_c   = self.hp.parse_hgvs_variant(mosaic_c)
        var_chimeric_c = self.hp.parse_hgvs_variant(chimeric_c)
        
        var_compound_g = self.vm.c_to_g(var_compound_c, 'NC_000023.10')
        var_mosaic_g   = self.vm.c_to_g(var_mosaic_c, 'NC_000023.10')
        var_chimeric_g = self.vm.c_to_g(var_chimeric_c, 'NC_000023.10')
        
        self.assertEqual(str(var_compound_g), 'NC_000023.10:g.[107829929C>T;107939544_107939551del]')
        self.assertEqual(str(var_mosaic_g),   'NC_000023.10:g.[=/107829929C>T]')
        self.assertEqual(str(var_chimeric_g), 'NC_000023.10:g.[=//107829929C>T]')

    def test_gcrp_invalid_input_type(self):
        hgvs_g = 'NC_000007.13:g.36561662C>T'
        hgvs_c = 'NM_001637.3:c.1582G>A'

        var_g = self.hp.parse_hgvs_variant(hgvs_g)
        var_c = self.hp.parse_hgvs_variant(hgvs_c)

        cases = {
            'gc': (self.vm.g_to_c, (var_c, 'NM_001637.3')),
            'gr': (self.vm.g_to_n, (var_c, 'NM_001637.3')),
            'rg': (self.vm.n_to_g, (var_c, 'NM_001637.3')),
            'cg': (self.vm.c_to_g, (var_g, 'NM_001637.3')),
            'cr': (self.vm.c_to_n, (var_g, )),
            'rc': (self.vm.n_to_c, (var_g, )),
            'cp': (self.vm.c_to_p, (var_g, None)),
        }

        failures = []
        for key in cases:
            try:
                func, args = cases[key]
                var_result = func(*args)
                failures.append(key)
            except hgvs.exceptions.HGVSInvalidVariantError:
                pass

        self.assertFalse(failures, "conversions not failing: {}".format(failures))

    def test_gc_invalid_input_nm_accession(self):
        hgvs_g = 'NC_000007.13:g.36561662C>T'
        var_g = self.hp.parse_hgvs_variant(hgvs_g)
        with self.assertRaises(hgvs.exceptions.HGVSError):
            var_p = self.vm.c_to_p(var_g, 'NM_999999.1')





class Test_RefReplacement(unittest.TestCase):
    test_cases = [
        # These casese attempt to test reference update in four dimensions:
        # - variant type: n, c, g
        # - major mapping paths: c<->n, c<->g, n<->g
        # - variant class: sub, del, ins, delins, dup
        # - strand: +/-

        # ADRB2    │ NM_000024.5 │  239 │ 1481 │ NC_000005.9  │  1 │ 148206155,148208197 | 284=1X32=1X1724=
        # cseq = hdp.fetch_seq('NM_000024.5')
        # gseq = hdp.fetch_seq('NC_000005.9',148206155,148208197)
        # cseq[280:290] = 'CAATAGAAGC'
        # gseq[280:290] = 'CAATGGAAGC'
        #                      ^ @ n.285
        # These variants are in and around the first sub: 
        {u'c': 'NM_000024.5:c.42C>N',  u'g': 'NC_000005.9:g.148206436C>N',  u'n': u'NM_000024.5:n.281C>N'},
        {u'c': 'NM_000024.5:c.43A>N',  u'g': 'NC_000005.9:g.148206437A>N',  u'n': u'NM_000024.5:n.282A>N'},
        {u'c': 'NM_000024.5:c.44A>N',  u'g': 'NC_000005.9:g.148206438A>N',  u'n': u'NM_000024.5:n.283A>N'},
        {u'c': 'NM_000024.5:c.45T>N',  u'g': 'NC_000005.9:g.148206439T>N',  u'n': u'NM_000024.5:n.284T>N'},
        {u'c': 'NM_000024.5:c.46A>N',  u'g': 'NC_000005.9:g.148206440G>N',  u'n': u'NM_000024.5:n.285A>N'}, # ref repl
        {u'c': 'NM_000024.5:c.47G>N',  u'g': 'NC_000005.9:g.148206441G>N',  u'n': u'NM_000024.5:n.286G>N'},
        {u'c': 'NM_000024.5:c.48A>N',  u'g': 'NC_000005.9:g.148206442A>N',  u'n': u'NM_000024.5:n.287A>N'},
        {u'c': 'NM_000024.5:c.49A>N',  u'g': 'NC_000005.9:g.148206443A>N',  u'n': u'NM_000024.5:n.288A>N'},
        {u'c': 'NM_000024.5:c.50G>N',  u'g': 'NC_000005.9:g.148206444G>N',  u'n': u'NM_000024.5:n.289G>N'},
        {u'c': 'NM_000024.5:c.51C>N',  u'g': 'NC_000005.9:g.148206445C>N',  u'n': u'NM_000024.5:n.290C>N'},

        # ins, del, delins, dup:
        {u'c': 'NM_000024.5:c.46_47insNN',  u'g': 'NC_000005.9:g.148206440_148206441insNN',  u'n': 'NM_000024.5:n.285_286insNN'},
        {u'c': 'NM_000024.5:c.45_47delTAG',  u'g': 'NC_000005.9:g.148206439_148206441delTGG',  u'n': 'NM_000024.5:n.284_286delTAG'},
        {u'c': 'NM_000024.5:c.45_47delTAGinsNNNN',  u'g': 'NC_000005.9:g.148206439_148206441delTGGinsNNNN',  u'n': 'NM_000024.5:n.284_286delTAGinsNNNN'},
        {u'c': 'NM_000024.5:c.45_47delTAGinsNNNN',  u'g': 'NC_000005.9:g.148206439_148206441delTGGinsNNNN',  u'n': 'NM_000024.5:n.284_286delTAGinsNNNN'},
        {u'c': 'NM_000024.5:c.46dupA',  u'g': 'NC_000005.9:g.148206440dupG',  u'n': 'NM_000024.5:n.285dupA'},


        # IFNA16   │ NM_002173.2 │    6 │  576 │ NC_000009.11 │ -1 │  21216371, 21217310 | 691=2X246=
        # cseq = hdp.fetch_seq('NM_002173.2')
        # gseq = reverse_complement(hdp.fetch_seq('NC_000009.11',21216371,21217310))
        # cseq[685:695] = 'AAATTTCAAA'
        # gseq[685:695] = 'AAATTTTCAA'
        #                        ^^ @ n.692_693
        # These variants are in and around the 2X substitution
        {u'c': 'NM_002173.2:c.*110A>N',  u'g': 'NC_000009.11:g.21216625T>N',  u'n': u'NM_002173.2:n.686A>N'},
        {u'c': 'NM_002173.2:c.*111A>N',  u'g': 'NC_000009.11:g.21216624T>N',  u'n': u'NM_002173.2:n.687A>N'},
        {u'c': 'NM_002173.2:c.*112A>N',  u'g': 'NC_000009.11:g.21216623T>N',  u'n': u'NM_002173.2:n.688A>N'},
        {u'c': 'NM_002173.2:c.*113T>N',  u'g': 'NC_000009.11:g.21216622A>N',  u'n': u'NM_002173.2:n.689T>N'},
        {u'c': 'NM_002173.2:c.*114T>N',  u'g': 'NC_000009.11:g.21216621A>N',  u'n': u'NM_002173.2:n.690T>N'},
        {u'c': 'NM_002173.2:c.*115T>N',  u'g': 'NC_000009.11:g.21216620A>N',  u'n': u'NM_002173.2:n.691T>N'},
        {u'c': 'NM_002173.2:c.*116C>N',  u'g': 'NC_000009.11:g.21216619A>N',  u'n': u'NM_002173.2:n.692C>N'}, # ref repl
        {u'c': 'NM_002173.2:c.*117A>N',  u'g': 'NC_000009.11:g.21216618G>N',  u'n': u'NM_002173.2:n.693A>N'}, # ref repl
        {u'c': 'NM_002173.2:c.*118A>N',  u'g': 'NC_000009.11:g.21216617T>N',  u'n': u'NM_002173.2:n.694A>N'},
        {u'c': 'NM_002173.2:c.*119A>N',  u'g': 'NC_000009.11:g.21216616T>N',  u'n': u'NM_002173.2:n.695A>N'},

        # ins, del, delins, dup:
        {u'c': 'NM_002173.2:c.*115_*117insNN',  u'g': 'NC_000009.11:g.21216618_21216620insNN',  u'n': 'NM_002173.2:n.691_693insNN'},
        {u'c': 'NM_002173.2:c.*114_*117delTTCA',  u'g': 'NC_000009.11:g.21216618_21216621delGAAA',  u'n': 'NM_002173.2:n.690_693delTTCA'},
        {u'c': 'NM_002173.2:c.*115_*117delTCAinsNN',  u'g': 'NC_000009.11:g.21216618_21216620delGAAinsNN',  u'n': 'NM_002173.2:n.691_693delTCAinsNN'},
        {u'c': 'NM_002173.2:c.*115_*117delTCAinsNN',  u'g': 'NC_000009.11:g.21216618_21216620delGAAinsNN',  u'n': 'NM_002173.2:n.691_693delTCAinsNN'},
        {u'c': 'NM_002173.2:c.*115_*117dupTCA',  u'g': 'NC_000009.11:g.21216618_21216620dupGAA',  u'n': 'NM_002173.2:n.691_693dupTCA'},
    ]


    def setUp(self):
        def _parse_rec(rec):
            rec['pv'] = {x: self.hp.parse_hgvs_variant(rec[x]) for x in 'cgn'}
            return rec

        self.hdp = hgvs.dataproviders.uta.connect()
        self.evm = hgvs.variantmapper.EasyVariantMapper(self.hdp, primary_assembly='GRCh37', alt_aln_method='splign')
        self.hp = hgvs.parser.Parser()
        self.tests = [_parse_rec(rec) for rec in self.test_cases]

    def test_replace_reference_sequence(self):
        """Replacing reference sequence in parsed variants"""

        for rec in self.tests:
            for x in 'cgn':
                pv = rec['pv'][x]
                if pv.posedit.edit.ref:
                    # replace ref with junk
                    pv.posedit.edit.ref = 'NNNNNN'
                self.evm._replace_reference(pv)
                self.assertEqual(rec[x], str(pv))


@attr(tags=["quick"])
class Test_EasyVariantMapper(unittest.TestCase):
    def setUp(self):
        self.hdp = hgvs.dataproviders.uta.connect()
        self.evm = hgvs.variantmapper.EasyVariantMapper(self.hdp, primary_assembly='GRCh37', alt_aln_method='splign')
        self.hgvs = {
            'g': 'NC_000007.13:g.36561662C>T',
            'c': 'NM_001637.3:c.1582G>A',
            'n': 'NM_001637.3:n.1983G>A',    # treat as non-coding, relative to tx start
            'p': 'NP_001628.1:p.(Gly528Arg)'
        }
        hp = hgvs.parser.Parser()
        self.var = {k: hp.parse_hgvs_variant(v) for k, v in self.hgvs.iteritems()}

    def test_c_to_g(self):
        self.assertEqual(self.hgvs['g'], str(self.evm.c_to_g(self.var['c'])))

    def test_c_to_n(self):
        self.assertEqual(self.hgvs['n'], str(self.evm.c_to_n(self.var['c'])))

    def test_g_to_c(self):
        self.assertEqual(self.hgvs['c'], str(self.evm.g_to_c(self.var['g'], self.var['c'].ac)))

    def test_g_to_n(self):
        self.assertEqual(self.hgvs['n'], str(self.evm.g_to_n(self.var['g'], self.var['n'].ac)))

    def test_c_to_p(self):
        self.assertEqual(self.hgvs['p'], str(self.evm.c_to_p(self.var['c'])))


if __name__ == '__main__':
    unittest.main()

## <LICENSE>
## Copyright 2014 HGVS Contributors (https://bitbucket.org/biocommons/hgvs)
## 
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
## 
##     http://www.apache.org/licenses/LICENSE-2.0
## 
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
## </LICENSE>

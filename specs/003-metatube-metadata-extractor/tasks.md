# 浠诲姟: MetaTube 鍏冩暟鎹彁鍙栧櫒绉绘 (v0.4.0)

**杈撳叆**: 鏉ヨ嚜 `/specs/003-metatube-metadata-extractor/` 鐨勮璁℃枃妗?
**鍓嶇疆鏉′欢**: plan.md(蹇呴渶), spec.md(蹇呴渶)

**娴嬭瘯**: 鍔熻兘瑙勮寖鏄庣‘瑕佹眰鍗曞厓娴嬭瘯锛圡ock HTTP 鍝嶅簲锛岀撼鍏?CI锛夛紝鍥犳姣忎釜鎻愬彇鍣ㄥ潎鏈夊搴旀祴璇曚换鍔°€傞泦鎴愭祴璇曪紙鐪熷疄缃戠粶锛夊彲閫夛紝涓嶅垪鍏?CI銆?

**缁勭粐缁撴瀯**: 浠诲姟鎸夌敤鎴锋晠浜嬪垎缁勩€俇S1锛堟柊绔欑偣绉绘锛夋寜鎵规锛圓/B/C/D锛夌粏鍒嗭紝姣忔壒娆″彲鐙珛瀹炴柦鍜屾祴璇曘€?

## 鏍煎紡: `[ID] [P?] [Story] 鎻忚堪`
- **[P]**: 鍙互骞惰杩愯锛堜笉鍚屾枃浠讹紝鏃犱緷璧栧叧绯伙級
- **[Story]**: 姝や换鍔″睘浜庡摢涓敤鎴锋晠浜嬶紙US1/US2/US3锛?
- 鍦ㄦ弿杩颁腑鍖呭惈纭垏鐨勬枃浠惰矾寰?

## 璺緞绾﹀畾
- **婧愮爜**: `pavone/plugins/metadata/`锛堟彁鍙栧櫒锛?
- **娴嬭瘯**: `tests/metadata/`锛圡ock 鍗曞厓娴嬭瘯锛?
- **鍙傝€冩簮鐮?*: `D:\code\metatube-sdk-go-main\provider\<site>\<site>.go`

---

## 闃舵 1: 璁剧疆

**鐩殑**: 鍒涘缓娴嬭瘯鍩虹璁炬柦锛屼负鎵€鏈夋彁鍙栧櫒娴嬭瘯鎻愪緵鍏变韩 fixture

- [X] T001 鍦?`tests/metadata/` 鐩綍涓嬪垱寤?`__init__.py`锛堢┖鏂囦欢锛夊拰 `conftest.py`锛屽湪 conftest.py 涓畾涔夊叡浜?fixture锛歚mock_response(html_content, status_code=200)` 鐢ㄤ簬 Mock requests.get 杩斿洖鍊硷紝`mock_json_response(data, status_code=200)` 鐢ㄤ簬 Mock JSON API 鍝嶅簲

---

## 闃舵 2: 鍩虹锛堥樆濉炲墠缃潯浠讹級

**鐩殑**: 楠岃瘉鐜版湁鎻愬彇鍣ㄦ棤鍥炲綊锛岀‘璁ゆ彃浠惰嚜鍔ㄥ彂鐜版満鍒舵甯稿伐浣?

**鈿狅笍 鍏抽敭**: 鍦ㄦ闃舵纭閫氳繃鍚庯紝鏂瑰彲寮€濮嬫壒娆?A 瀹炴柦

- [X] T002 杩愯 `pytest tests/ -v` 纭鎵€鏈夌幇鏈夋祴璇曢€氳繃锛堝熀鍑嗙嚎锛夛紝璁板綍褰撳墠娴嬭瘯鏁伴噺锛岀‘璁?CaribbeancOM銆丱nePondo銆丼upFC2銆丳PVDataBank 鐨勭幇鏈夋彁鍙栧櫒鍙互閫氳繃 PluginManager 姝ｅ父鍔犺浇

**妫€鏌ョ偣**: 鍩哄噯娴嬭瘯鍏ㄩ€氳繃锛岃嚜鍔ㄥ彂鐜版満鍒跺伐浣滄甯?鉁?

---

## 闃舵 3: 鐢ㄦ埛鏁呬簨 1 鈥?鎵规 A锛氱Щ妞嶉鎵?8 涓珯鐐?(浼樺厛绾? P1) 馃幆 MVP

**鐩爣**: 绉绘 10musume銆乤v-league銆乤vbase銆乤ventertainments銆乧0930銆乨ahlia銆乨uga銆乫aleno 鍏?8 涓珯鐐圭殑鍏冩暟鎹彁鍙栧櫒

**鐙珛娴嬭瘯**: 瀵规瘡涓柊鎻愬彇鍣紝浣跨敤 Mock HTML/JSON 鍝嶅簲楠岃瘉鑳芥纭繑鍥?`MovieMetadata`锛屼笖 `can_extract()` 瀵瑰悎娉?URL 杩斿洖 True銆佸闈炴湰绔?URL 杩斿洖 False

### 鎵规 A 娴嬭瘯锛圡ock 鍗曞厓娴嬭瘯锛岀撼鍏?CI锛?

- [X] T003 [P] [US1] 鍦?`tests/metadata/test_tenmusume.py` 涓负 `TenMusumeMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇?`can_extract` 璇嗗埆 10musume.com 鍩熷悕銆丮ock HTML 鍝嶅簲楠岃瘉 `extract_metadata` 杩斿洖鍚?title/actors/tags 鐨?`MovieMetadata`
- [X] T004 [P] [US1] 鍦?`tests/metadata/test_avleague.py` 涓负 `AvLeagueMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇?`can_extract` 璇嗗埆 av-league.com 鍩熷悕銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata` 杩斿洖 `MovieMetadata`
- [X] T005 [P] [US1] 鍦?`tests/metadata/test_avbase.py` 涓负 `AvBaseMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇?`can_extract` 璇嗗埆 avbase.one 鍩熷悕锛堝惈 API 璋冪敤鍦烘櫙锛夈€丮ock JSON 鍝嶅簲楠岃瘉 `extract_metadata` 杩斿洖 `MovieMetadata`
- [X] T006 [P] [US1] 鍦?`tests/metadata/test_aventertainments.py` 涓负 `AvEntertainmentsMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇?`can_extract`銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata` 杩斿洖 `MovieMetadata`
- [X] T007 [P] [US1] 鍦?`tests/metadata/test_c0930.py` 涓负 `C0930Metadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇?`can_extract` 璇嗗埆 c0930.com銆丮ock HTML 楠岃瘉 `extract_metadata`
- [X] T008 [P] [US1] 鍦?`tests/metadata/test_dahlia.py` 涓负 `DahliaMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇?`can_extract` 璇嗗埆 dahlia-av.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T009 [P] [US1] 鍦?`tests/metadata/test_duga.py` 涓负 `DugaMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇?`can_extract` 璇嗗埆 duga.jp銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T010 [P] [US1] 鍦?`tests/metadata/test_faleno.py` 涓负 `FalenoMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇?`can_extract` 璇嗗埆 faleno.jp銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`

### 鎵规 A 瀹炴柦

- [X] T011 [P] [US1] 鍦?`pavone/plugins/metadata/tenmusume_metadata.py` 涓疄鐜?`TenMusumeMetadata`锛氱户鎵?`MetadataPlugin`锛屽弬鑰?`D:\code\metatube-sdk-go-main\provider\10musume\10musume.go` 瀹炵幇 URL 璇嗗埆銆両D 瑙ｆ瀽銆丠TML 鎶撳彇涓庡瓧娈垫槧灏勶紝杩斿洖 `MovieMetadata`
- [X] T012 [P] [US1] 鍦?`pavone/plugins/metadata/avleague_metadata.py` 涓疄鐜?`AvLeagueMetadata`锛氬弬鑰?`provider\av-league\av-league.go` 瀹炵幇 av-league.com 鍏冩暟鎹彁鍙?
- [X] T013 [P] [US1] 鍦?`pavone/plugins/metadata/avbase_metadata.py` 涓疄鐜?`AvBaseMetadata`锛氬弬鑰?`provider\avbase\avbase.go`锛屾敮鎸?avbase.one API锛圝SON 鍝嶅簲锛夛紝瀹炵幇瀛楁鏄犲皠
- [X] T014 [P] [US1] 鍦?`pavone/plugins/metadata/aventertainments_metadata.py` 涓疄鐜?`AvEntertainmentsMetadata`锛氬弬鑰?`provider\aventertainments\aventertainments.go` 瀹炵幇 aventertainments.com 鍏冩暟鎹彁鍙?
- [X] T015 [P] [US1] 鍦?`pavone/plugins/metadata/c0930_metadata.py` 涓疄鐜?`C0930Metadata`锛氬弬鑰?`provider\c0930\c0930.go` 瀹炵幇 c0930.com 鍏冩暟鎹彁鍙?
- [X] T016 [P] [US1] 鍦?`pavone/plugins/metadata/dahlia_metadata.py` 涓疄鐜?`DahliaMetadata`锛氬弬鑰?`provider\dahlia\dahlia.go` 瀹炵幇 dahlia-av.com 鍏冩暟鎹彁鍙?
- [X] T017 [P] [US1] 鍦?`pavone/plugins/metadata/duga_metadata.py` 涓疄鐜?`DugaMetadata`锛氬弬鑰?`provider\duga\duga.go` 瀹炵幇 duga.jp 鍏冩暟鎹彁鍙?
- [X] T018 [P] [US1] 鍦?`pavone/plugins/metadata/faleno_metadata.py` 涓疄鐜?`FalenoMetadata`锛氬弬鑰?`provider\faleno\faleno.go` 瀹炵幇 faleno.jp 鍏冩暟鎹彁鍙?
- [X] T019 [US1] 鍦?`pavone/plugins/metadata/__init__.py` 涓鍏ユ壒娆?A 鍏ㄩ儴 8 涓柊鎻愬彇鍣ㄧ被锛屾坊鍔犲埌 `__all__` 鍒楄〃

**妫€鏌ョ偣**: 杩愯 `pytest tests/ -v`锛屾壒娆?A 鎵€鏈夊崟鍏冩祴璇曢€氳繃锛岀幇鏈夋彁鍙栧櫒鏃犲洖褰?鉁?

---

## 闃舵 4: 鐢ㄦ埛鏁呬簨 1 鈥?鎵规 B锛氱Щ妞嶇浜屾壒 8 涓珯鐐?(浼樺厛绾? P1)

**鐩爣**: 绉绘 fanza銆乫c2hub銆乫c2ppvdb銆乬colle銆乬etchu銆乬friends銆乭0930銆乭4610 鍏?8 涓珯鐐?

**鐙珛娴嬭瘯**: 鍚屾壒娆?A锛屾瘡涓彁鍙栧櫒 Mock 鍗曞厓娴嬭瘯鐙珛閫氳繃

### 鎵规 B 娴嬭瘯

- [X] T020 [P] [US1] 鍦?`tests/metadata/test_fanza.py` 涓负 `FanzaMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?dmm.co.jp/fanza.com 鍩熷悕銆丮ock 鍝嶅簲楠岃瘉瀛楁鏄犲皠锛堟敞鎰?dmm 闇€瑕佺櫥褰曟€佺殑 cookie mock锛?
- [X] T021 [P] [US1] 鍦?`tests/metadata/test_fc2hub.py` 涓负 `Fc2HubMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?fc2hub.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T022 [P] [US1] 鍦?`tests/metadata/test_fc2ppvdb.py` 涓负 `Fc2PpvdbMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?fc2ppvdb.com銆丮ock JSON API 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T023 [P] [US1] 鍦?`tests/metadata/test_gcolle.py` 涓负 `GcolleMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?gcolle.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T024 [P] [US1] 鍦?`tests/metadata/test_getchu.py` 涓负 `GetchuMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?getchu.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T025 [P] [US1] 鍦?`tests/metadata/test_gfriends.py` 涓负 `GfriendsMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?gfriends.io銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`锛坓friends 涓烘紨鍛樺ご鍍忔暟鎹簱锛屾祴璇曞浘鐗?URL 杩斿洖锛?
- [X] T026 [P] [US1] 鍦?`tests/metadata/test_h0930.py` 涓负 `H0930Metadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?h0930.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T027 [P] [US1] 鍦?`tests/metadata/test_h4610.py` 涓负 `H4610Metadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?h4610.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`

### 鎵规 B 瀹炴柦

- [X] T028 [P] [US1] 鍦?`pavone/plugins/metadata/fanza_metadata.py` 涓疄鐜?`FanzaMetadata`锛氬弬鑰?`provider\fanza\fanza.go` 瀹炵幇 dmm.co.jp/fanza.com 鍏冩暟鎹彁鍙栵紙娉ㄦ剰 DMM API 鍙傛暟鍜屽尯鍩熼檺鍒跺鐞嗭級
- [X] T029 [P] [US1] 鍦?`pavone/plugins/metadata/fc2hub_metadata.py` 涓疄鐜?`Fc2HubMetadata`锛氬弬鑰?`provider\fc2hub\fc2hub.go` 瀹炵幇 fc2hub.com 鍏冩暟鎹彁鍙?
- [X] T030 [P] [US1] 鍦?`pavone/plugins/metadata/fc2ppvdb_metadata.py` 涓疄鐜?`Fc2PpvdbMetadata`锛氬弬鑰?`provider\fc2ppvdb\fc2ppvdb.go` 瀹炵幇 fc2ppvdb.com API 璋冪敤涓庡瓧娈垫槧灏?
- [X] T031 [P] [US1] 鍦?`pavone/plugins/metadata/gcolle_metadata.py` 涓疄鐜?`GcolleMetadata`锛氬弬鑰?`provider\gcolle\gcolle.go` 瀹炵幇 gcolle.com 鍏冩暟鎹彁鍙?
- [X] T032 [P] [US1] 鍦?`pavone/plugins/metadata/getchu_metadata.py` 涓疄鐜?`GetchuMetadata`锛氬弬鑰?`provider\getchu\getchu.go` 瀹炵幇 getchu.com 鍏冩暟鎹彁鍙?
- [X] T033 [P] [US1] 鍦?`pavone/plugins/metadata/gfriends_metadata.py` 涓疄鐜?`GfriendsMetadata`锛氬弬鑰?`provider\gfriends\gfriends.go` 瀹炵幇 gfriends.io 婕斿憳澶村儚鏁版嵁鎻愬彇锛堢壒娈婏細姝?provider 涓烘紨鍛樺浘鐗囨暟鎹簱锛宑over/thumbnail 瀛楁涓哄ご鍍?URL锛屽叾浣欏瓧娈垫寜瑙勮寖濉?None锛?
- [X] T034 [P] [US1] 鍦?`pavone/plugins/metadata/h0930_metadata.py` 涓疄鐜?`H0930Metadata`锛氬弬鑰?`provider\h0930\h0930.go` 瀹炵幇 h0930.com 鍏冩暟鎹彁鍙?
- [X] T035 [P] [US1] 鍦?`pavone/plugins/metadata/h4610_metadata.py` 涓疄鐜?`H4610Metadata`锛氬弬鑰?`provider\h4610\h4610.go` 瀹炵幇 h4610.com 鍏冩暟鎹彁鍙?
- [X] T036 [US1] 鍦?`pavone/plugins/metadata/__init__.py` 涓鍏ユ壒娆?B 鍏ㄩ儴 8 涓柊鎻愬彇鍣ㄧ被锛屾坊鍔犲埌 `__all__` 鍒楄〃

**妫€鏌ョ偣**: 杩愯 `pytest tests/ -v`锛屾壒娆?A+B 鎵€鏈夊崟鍏冩祴璇曢€氳繃锛岀幇鏈夋彁鍙栧櫒鏃犲洖褰?鉁?

---

## 闃舵 5: 鐢ㄦ埛鏁呬簨 1 鈥?鎵规 C锛氱Щ妞嶇涓夋壒 8 涓珯鐐?(浼樺厛绾? P1)

**鐩爣**: 绉绘 heydouga銆乭eyzo銆乯av321銆乯avbus銆乯avfree銆乲in8tengoku銆乵adouqu銆乵gstage 鍏?8 涓珯鐐?

**鐙珛娴嬭瘯**: 姣忎釜鎻愬彇鍣?Mock 鍗曞厓娴嬭瘯鐙珛閫氳繃

### 鎵规 C 娴嬭瘯

- [X] T037 [P] [US1] 鍦?`tests/metadata/test_heydouga.py` 涓负 `HeydougaMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?heydouga.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T038 [P] [US1] 鍦?`tests/metadata/test_heyzo.py` 涓负 `HeyzoMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?heyzo.com銆丮ock JSON API 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T039 [P] [US1] 鍦?`tests/metadata/test_jav321.py` 涓负 `Jav321Metadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?jav321.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`锛堟敞鎰?jav321 涓鸿仛鍚堟暟鎹簱锛屽瓧娈佃鐩栫巼楂橈級
- [X] T040 [P] [US1] 鍦?`tests/metadata/test_javbus.py` 涓负 `JavbusMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?javbus.com銆丮ock 鍝嶅簲楠岃瘉鍚鍔涢摼 tag 鐨?`extract_metadata`
- [X] T041 [P] [US1] 鍦?`tests/metadata/test_javfree.py` 涓负 `JavfreeMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?javfree.sh銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T042 [P] [US1] 鍦?`tests/metadata/test_kin8tengoku.py` 涓负 `Kin8tengokuMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?kin8tengoku.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T043 [P] [US1] 鍦?`tests/metadata/test_madouqu.py` 涓负 `MadouquMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?madouqu.com锛堜腑鏂囩珯鐐?API锛夈€丮ock JSON 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T044 [P] [US1] 鍦?`tests/metadata/test_mgstage.py` 涓负 `MgstageMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?mgstage.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`锛堟敞鎰?mgstage 闇€瑕?R18 cookie mock锛?

### 鎵规 C 瀹炴柦

- [X] T045 [P] [US1] 鍦?`pavone/plugins/metadata/heydouga_metadata.py` 涓疄鐜?`HeydougaMetadata`锛氬弬鑰?`provider\heydouga\heydouga.go` 瀹炵幇 heydouga.com 鍏冩暟鎹彁鍙?
- [X] T046 [P] [US1] 鍦?`pavone/plugins/metadata/heyzo_metadata.py` 涓疄鐜?`HeyzoMetadata`锛氬弬鑰?`provider\heyzo\heyzo.go` 瀹炵幇 heyzo.com API 璋冪敤锛圝SON锛変笌瀛楁鏄犲皠
- [X] T047 [P] [US1] 鍦?`pavone/plugins/metadata/jav321_metadata.py` 涓疄鐜?`Jav321Metadata`锛氬弬鑰?`provider\jav321\jav321.go` 瀹炵幇 jav321.com HTML 瑙ｆ瀽
- [X] T048 [P] [US1] 鍦?`pavone/plugins/metadata/javbus_metadata.py` 涓疄鐜?`JavbusMetadata`锛氬弬鑰?`provider\javbus\javbus.go` 瀹炵幇 javbus.com HTML 瑙ｆ瀽涓庡瓧娈垫槧灏?
- [X] T049 [P] [US1] 鍦?`pavone/plugins/metadata/javfree_metadata.py` 涓疄鐜?`JavfreeMetadata`锛氬弬鑰?`provider\javfree\javfree.go` 瀹炵幇 javfree.sh 鍏冩暟鎹彁鍙?
- [X] T050 [P] [US1] 鍦?`pavone/plugins/metadata/kin8tengoku_metadata.py` 涓疄鐜?`Kin8tengokuMetadata`锛氬弬鑰?`provider\kin8tengoku\kin8tengoku.go` 瀹炵幇 kin8tengoku.com 鍏冩暟鎹彁鍙?
- [X] T051 [P] [US1] 鍦?`pavone/plugins/metadata/madouqu_metadata.py` 涓疄鐜?`MadouquMetadata`锛氬弬鑰?`provider\madouqu\madouqu.go` 瀹炵幇 madouqu.com API锛堜腑鏂囧唴瀹癸級瀛楁鏄犲皠
- [X] T052 [P] [US1] 鍦?`pavone/plugins/metadata/mgstage_metadata.py` 涓疄鐜?`MgstageMetadata`锛氬弬鑰?`provider\mgstage\mgstage.go` 瀹炵幇 mgstage.com HTML 瑙ｆ瀽锛堟敞鎰忓勾榫勯獙璇?cookie 璁剧疆锛?
- [X] T053 [US1] 鍦?`pavone/plugins/metadata/__init__.py` 涓鍏ユ壒娆?C 鍏ㄩ儴 8 涓柊鎻愬彇鍣ㄧ被锛屾坊鍔犲埌 `__all__` 鍒楄〃

**妫€鏌ョ偣**: 杩愯 `pytest tests/ -v`锛屾壒娆?A+B+C 鎵€鏈夊崟鍏冩祴璇曢€氳繃锛岀幇鏈夋彁鍙栧櫒鏃犲洖褰?鉁?

---

## 闃舵 6: 鐢ㄦ埛鏁呬簨 1 鈥?鎵规 D锛氱Щ妞嶆渶鍚?8 涓珯鐐?(浼樺厛绾? P1)

**鐩爣**: 绉绘 modelmediaasia銆乵uramura銆乵ywife銆乸acopacomama銆乸colle銆乻od銆乼heporndb銆乼okyo-hot 鍏?8 涓珯鐐?

**鐙珛娴嬭瘯**: 姣忎釜鎻愬彇鍣?Mock 鍗曞厓娴嬭瘯鐙珛閫氳繃

### 鎵规 D 娴嬭瘯

- [X] T054 [P] [US1] 鍦?`tests/metadata/test_modelmediaasia.py` 涓负 `ModelMediaAsiaMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?modelmediaasia.com锛堝惈 JSON API锛夈€丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T055 [P] [US1] 鍦?`tests/metadata/test_muramura.py` 涓负 `MuramuraMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?muramura.tv銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T056 [P] [US1] 鍦?`tests/metadata/test_mywife.py` 涓负 `MyWifeMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?mywife.co.jp銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T057 [P] [US1] 鍦?`tests/metadata/test_pacopacomama.py` 涓负 `PacopacomamaMeta` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?pacopacomama.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T058 [P] [US1] 鍦?`tests/metadata/test_pcolle.py` 涓负 `PcolleMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?pcolle.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T059 [P] [US1] 鍦?`tests/metadata/test_sod.py` 涓负 `SodMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?sod.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`
- [X] T060 [P] [US1] 鍦?`tests/metadata/test_theporndb.py` 涓负 `ThePorndbMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?theporndb.net锛圧EST API锛夈€丮ock JSON 鍝嶅簲楠岃瘉 `extract_metadata`锛堟敞鎰?API Key 閫氳繃 config 娉ㄥ叆锛?
- [X] T061 [P] [US1] 鍦?`tests/metadata/test_tokyohot.py` 涓负 `TokyoHotMetadata` 缂栧啓鍗曞厓娴嬭瘯锛氶獙璇佽瘑鍒?tokyo-hot.com銆丮ock 鍝嶅簲楠岃瘉 `extract_metadata`

### 鎵规 D 瀹炴柦

- [X] T062 [P] [US1] 鍦?`pavone/plugins/metadata/modelmediaasia_metadata.py` 涓疄鐜?`ModelMediaAsiaMetadata`锛氬弬鑰?`provider\modelmediaasia\modelmediaasia.go` 鍜?`responses.go` 瀹炵幇 modelmediaasia.com API 璋冪敤涓庡瓧娈垫槧灏?
- [X] T063 [P] [US1] 鍦?`pavone/plugins/metadata/muramura_metadata.py` 涓疄鐜?`MuramuraMetadata`锛氬弬鑰?`provider\muramura\muramura.go` 瀹炵幇 muramura.tv 鍏冩暟鎹彁鍙?
- [X] T064 [P] [US1] 鍦?`pavone/plugins/metadata/mywife_metadata.py` 涓疄鐜?`MyWifeMetadata`锛氬弬鑰?`provider\mywife\mywife.go` 瀹炵幇 mywife.co.jp 鍏冩暟鎹彁鍙?
- [X] T065 [P] [US1] 鍦?`pavone/plugins/metadata/pacopacomama_metadata.py` 涓疄鐜?`PacopacomamaMeta`锛氬弬鑰?`provider\pacopacomama\pacopacomama.go` 瀹炵幇 pacopacomama.com 鍏冩暟鎹彁鍙?
- [X] T066 [P] [US1] 鍦?`pavone/plugins/metadata/pcolle_metadata.py` 涓疄鐜?`PcolleMetadata`锛氬弬鑰?`provider\pcolle\pcolle.go` 瀹炵幇 pcolle.com 鍏冩暟鎹彁鍙?
- [X] T067 [P] [US1] 鍦?`pavone/plugins/metadata/sod_metadata.py` 涓疄鐜?`SodMetadata`锛氬弬鑰?`provider\sod\sod.go` 瀹炵幇 sod.com 鍏冩暟鎹彁鍙?
- [X] T068 [P] [US1] 鍦?`pavone/plugins/metadata/theporndb_metadata.py` 涓疄鐜?`ThePorndbMetadata`锛氬弬鑰?`provider\theporndb\theporndb.go` 瀹炵幇 theporndb.net REST API 璋冪敤锛圓PI Key 浠?`self.config` 璇诲彇锛夛紝瀛楁鏄犲皠鍙傝€?`structs.go`
- [X] T069 [P] [US1] 鍦?`pavone/plugins/metadata/tokyohot_metadata.py` 涓疄鐜?`TokyoHotMetadata`锛氬弬鑰?`provider\tokyo-hot\tokyo-hot.go` 瀹炵幇 tokyo-hot.com 鍏冩暟鎹彁鍙?
- [X] T070 [US1] 鍦?`pavone/plugins/metadata/__init__.py` 涓鍏ユ壒娆?D 鍏ㄩ儴 8 涓柊鎻愬彇鍣ㄧ被锛屾坊鍔犲埌 `__all__` 鍒楄〃

**妫€鏌ョ偣**: 杩愯 `pytest tests/ -v`锛屽叏閮?32 涓柊鎻愬彇鍣ㄥ崟鍏冩祴璇曢€氳繃锛岀幇鏈夋彁鍙栧櫒鏃犲洖褰掞紝鎬荤珯鐐规暟閲忚揪鎴?SC-001锛堚墺5 涓級鉁?

---

## 闃舵 7: 鐢ㄦ埛鏁呬簨 2 鈥?缁撴瀯娓呮櫚涓庡彲缁存姢鎬?(浼樺厛绾? P2)

**鐩爣**: 纭繚绉绘浠ｇ爜缁撴瀯娓呮櫚銆佹槗浜庡悗缁淮鎶わ紝鏂板寮€鍙戣€呮枃妗?

**鐙珛娴嬭瘯**: 鏂板/淇敼浠绘剰涓€涓彁鍙栧櫒锛屽叾浠栨彁鍙栧櫒娴嬭瘯浠嶅叏閮ㄩ€氳繃

- [X] T071 [US2] 鍦?`pavone/plugins/metadata/base.py` 涓负 `MetadataPlugin` 鏂板 docstring 璇存槑绉绘鎻愬彇鍣ㄧ殑寮€鍙戣鑼冿細瀛楁鏄犲皠绾﹀畾銆佺己澶卞瓧娈靛鐞嗘柟寮忋€乣can_extract` 瀹炵幇瑕佹眰
- [X] T072 [P] [US2] 瀹℃煡鍏ㄩ儴 32 涓柊鎻愬彇鍣ㄦ枃浠讹紝纭繚姣忎釜鏂囦欢澶撮儴鍖呭惈锛氱珯鐐瑰悕绉般€丮etaTube 鍙傝€冭矾寰勩€佹敮鎸佺殑 URL 妯″紡娉ㄩ噴锛堝弬鑰?`caribbeancom_metadata.py` 鐨勬敞閲婇鏍硷級
- [X] T073 [US2] 楠岃瘉 `PluginManager._load_builtin_plugins()` 鑳借嚜鍔ㄥ彂鐜板叏閮?32 涓柊鎻愬彇鍣紙閫氳繃 `plugin_manager.metadata_plugins` 鍒楄〃闀垮害楠岃瘉锛夛紝鍦?`tests/test_plugin_manager.py` 涓坊鍔犳柇瑷€

**妫€鏌ョ偣**: 鏂板浠绘剰鎻愬彇鍣ㄦ枃浠跺悗锛宍PluginManager` 鏃犻渶淇敼鍗冲彲鑷姩鍙戠幇 鉁?

---

## 闃舵 8: 鐢ㄦ埛鏁呬簨 3 鈥?鍏煎鎬т笌閿欒澶勭悊 (浼樺厛绾? P3)

**鐩爣**: 涓嶆敮鎸佹垨寮傚父绔欑偣杩斿洖鏄庣‘閿欒鎻愮ず锛屼笉褰卞搷鏁翠綋娴佺▼

**鐙珛娴嬭瘯**: 杈撳叆鏈煡绔欑偣 URL锛岀郴缁熻繑鍥?None 鎴栧弸濂介敊璇紝涓嶆姏鍑烘湭鎹曡幏寮傚父

- [X] T074 [US3] 瀹℃煡鍏ㄩ儴 32 涓柊鎻愬彇鍣ㄧ殑 `extract_metadata()` 瀹炵幇锛岀‘淇濇墍鏈?HTTP 璇锋眰寮傚父锛坄requests.RequestException`锛夊潎琚崟鑾峰苟 `logger.error()` 璁板綍锛屾柟娉曡繑鍥?`None` 鑰岄潪鎶涘嚭寮傚父
- [X] T075 [P] [US3] 鍦?`tests/metadata/` 鍚勬祴璇曟枃浠朵腑涓烘瘡涓彁鍙栧櫒琛ュ厖閿欒鍦烘櫙娴嬭瘯锛歁ock 杩斿洖 404/缃戠粶寮傚父鏃?`extract_metadata` 杩斿洖 `None`锛孧ock 杩斿洖缁撴瀯寮傚父 HTML 鏃朵笉宕╂簝
- [X] T076 [US3] 瀹℃煡 `MetadataManager`锛坄pavone/manager/metadata_manager.py`锛変腑瀵?`extract_metadata` 杩斿洖 `None` 鐨勫鐞嗛€昏緫锛岀‘璁ゅ凡鏈?"鏆備笉鏀寔" 鎴栫被浼兼彁绀猴紝濡傛棤鍒欐坊鍔犲搴旂殑鏃ュ織杈撳嚭

**妫€鏌ョ偣**: 杩愯 `pytest tests/ -v`锛屾墍鏈夐敊璇満鏅祴璇曢€氳繃锛涜緭鍏ユ湭鐭ョ珯鐐规椂绯荤粺鏃ュ織杈撳嚭鏄庣‘鎻愮ず 鉁?

---

## 闃舵 9: 瀹屽杽涓庢í鍒囧叧娉ㄧ偣

**鐩爣**: 鏈€缁堟竻鐞嗐€佺増鏈彿鏇存柊銆佸洖褰掔‘璁?

- [X] T077 灏?`pavone/__init__.py` 涓殑 `__version__` 浠?`"0.3.x"` 鏇存柊涓?`"0.4.0"`锛屽悓姝ユ洿鏂?`pyproject.toml` 涓殑 `version` 瀛楁
- [X] T078 [P] 鍦?`CHANGELOG.md` 涓坊鍔?v0.4.0 鍙戝竷鏉＄洰锛屽垪鍑烘柊澧炵殑 32 涓珯鐐瑰厓鏁版嵁鎻愬彇鍣?
- [X] T079 杩愯瀹屾暣娴嬭瘯濂椾欢 `pytest tests/ -v --tb=short`锛岀‘璁ゅ叏閮ㄦ祴璇曢€氳繃锛屾棤鏂板璀﹀憡
- [ ] T080 [P] 鏇存柊 `docs/plugins/` 鎴?`README.md` 涓殑鏀寔绔欑偣鍒楄〃锛屾坊鍔犲叏閮?32 涓柊绔欑偣鐨勮鏄?

---

## 渚濊禆鍏崇郴鍥?

```
T001锛堣缃級
  鈹斺攢鈫?T002锛堝熀鍑嗛獙璇侊級
        鈹斺攢鈫?闃舵 3 鎵规 A锛圱003-T019锛?
              鈹斺攢鈫?闃舵 4 鎵规 B锛圱020-T036锛?
                    鈹斺攢鈫?闃舵 5 鎵规 C锛圱037-T053锛?
                          鈹斺攢鈫?闃舵 6 鎵规 D锛圱054-T070锛?
                                鈹斺攢鈫?闃舵 7 US2锛圱071-T073锛?
                                      鈹斺攢鈫?闃舵 8 US3锛圱074-T076锛?
                                            鈹斺攢鈫?闃舵 9 瀹屽杽锛圱077-T080锛?
```

**鎵规鍐呴儴**锛氬悓涓€鎵规鐨勬祴璇曚换鍔★紙T00x锛夊拰瀹炴柦浠诲姟锛圱01x锛夊潎鍙苟琛屾墽琛?[P]銆?

## 骞惰鎵ц绀轰緥锛堟壒娆?A锛?

```
寮€鍙戣€?A: T003 鈫?T011锛坱enmusume 娴嬭瘯 + 瀹炵幇锛?
寮€鍙戣€?B: T004 鈫?T012锛坅vleague 娴嬭瘯 + 瀹炵幇锛?
寮€鍙戣€?C: T005 鈫?T013锛坅vbase 娴嬭瘯 + 瀹炵幇锛?
寮€鍙戣€?D: T006 鈫?T014锛坅ventertainments 娴嬭瘯 + 瀹炵幇锛?
...锛堝悓鐞嗭級
鈫?姹囧悎锛歍019锛堟洿鏂?__init__.py锛夆啋 妫€鏌ョ偣
```

## 瀹炴柦绛栫暐

- **MVP**: 闃舵 3锛堟壒娆?A锛? 涓珯鐐癸級鈥?楠岃瘉鏁翠綋娴佺▼鍚庢帹杩涘悗缁壒娆?
- **澧為噺浜や粯**: 姣忔壒娆″彲鐙珛鍚堝苟 PR锛屾瘡鎵规缁撴潫鏃舵墽琛屾鏌ョ偣楠岃瘉
- **闆跺洖褰掍繚璇?*: 姣忔壒娆＄粨鏉熷墠蹇呴』杩愯 `pytest tests/ -v`锛岀‘璁ょ幇鏈夋彁鍙栧櫒鏃犲洖褰?

## 姹囨€?

| 鎸囨爣 | 鏁伴噺 |
|---|---|
| 鎬讳换鍔℃暟 | 80 |
| US1锛堢Щ妞嶇珯鐐癸級浠诲姟鏁?| 68锛圱003-T070锛?|
| US2锛堝彲缁存姢鎬э級浠诲姟鏁?| 3锛圱071-T073锛?|
| US3锛堥敊璇鐞嗭級浠诲姟鏁?| 3锛圱074-T076锛?|
| 璁剧疆 + 鍩虹 + 瀹屽杽 | 6锛圱001-T002, T077-T080锛?|
| 鍙苟琛屼换鍔★紙[P] 鏍囪锛?| 64 |
| 鏂扮Щ妞嶇珯鐐规暟 | 32 |
| MVP 鑼冨洿 | 鎵规 A锛? 涓珯鐐癸紝T001-T019锛?|

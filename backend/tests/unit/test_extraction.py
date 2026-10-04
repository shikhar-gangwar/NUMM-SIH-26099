from app.extraction.extractor import detect_category, extract_attributes

def test_category_detection():
    assert detect_category("HEXAGON HEAD BOLT M10X50") == "BOLT"
    assert detect_category("PIPE 4 INCH SCH 40") == "PIPE"
    assert detect_category("BEARING 6205 2RS") == "BEARING"
    assert detect_category("GATE VALVE 2 INCH CLASS 150") == "VALVE"
    assert detect_category("SPIRAL WOUND GASKET 4 INCH") == "GASKET"
    assert detect_category("CABLE 4C X 16 SQMM COPPER") == "CABLE"

def test_bolt_attribute_extraction():
    attrs = extract_attributes("BOLT HEX M10 X 50 STAINLESS STEEL 304 GRADE 8.8 IS 1363", "BOLT")
    attr_dict = {a.key: a for a in attrs}
    assert "fastener_type" in attr_dict
    assert attr_dict["fastener_type"].value_text == "HEX_BOLT"
    assert "nominal_diameter" in attr_dict
    assert attr_dict["nominal_diameter"].value_num == 10.0
    assert "property_class" in attr_dict
    assert attr_dict["property_class"].value_text == "8.8"

def test_pipe_attribute_extraction():
    attrs = extract_attributes("PIPE 4 INCH SCH 40 SEAMLESS A106 GR B", "PIPE")
    attr_dict = {a.key: a for a in attrs}
    assert "spec_grade" in attr_dict
    assert "manufacturing" in attr_dict
    assert attr_dict["manufacturing"].value_text == "SEAMLESS"

def test_bearing_attribute_extraction():
    attrs = extract_attributes("BEARING 6205 2RS C3 DEEP GROOVE BALL", "BEARING")
    attr_dict = {a.key: a for a in attrs}
    assert "designation_base" in attr_dict
    assert attr_dict["designation_base"].value_text == "6205"
    assert "seal_type" in attr_dict
    assert attr_dict["seal_type"].value_text == "2RS"

def test_valve_attribute_extraction():
    attrs = extract_attributes("GATE VALVE 2 INCH CLASS 150 FLANGED A216 WCB", "VALVE")
    attr_dict = {a.key: a for a in attrs}
    assert "valve_type" in attr_dict
    assert attr_dict["valve_type"].value_text == "GATE"
    assert "pressure_class" in attr_dict
    assert attr_dict["pressure_class"].value_text == "150"

def test_gasket_attribute_extraction():
    attrs = extract_attributes("SPIRAL WOUND GASKET 4 INCH CLASS 300 SS304", "GASKET")
    attr_dict = {a.key: a for a in attrs}
    assert "gasket_type" in attr_dict
    assert attr_dict["gasket_type"].value_text == "SPIRAL_WOUND"

def test_cable_attribute_extraction():
    attrs = extract_attributes("CABLE 4C X 16 SQMM COPPER XLPE 1.1KV ARMOURED", "CABLE")
    attr_dict = {a.key: a for a in attrs}
    assert "conductor_material" in attr_dict
    assert attr_dict["conductor_material"].value_text == "COPPER"
    assert "voltage_grade" in attr_dict
    assert attr_dict["voltage_grade"].value_text == "1.1KV"
    assert "insulation" in attr_dict
    assert attr_dict["insulation"].value_text == "XLPE"

def test_v2_expanded_attribute_extraction():
    # Bolt coating & standard
    bolt_attrs = {a.key: a for a in extract_attributes("HEX HEAD BOLT M16 X 70 8.8 HDG ASTM A193", "BOLT")}
    assert bolt_attrs["coating"].value_text == "HDG"
    assert bolt_attrs["coating"].rule_id == "bolt_coating"
    assert "ASTM A193" in bolt_attrs["standard"].value_text

    # Pipe end finish
    pipe_attrs = {a.key: a for a in extract_attributes("PIPE 6 INCH SCH 80 SEAMLESS BEVELED END A106 GR B", "PIPE")}
    assert pipe_attrs["end_finish"].value_text == "BEVELED"
    assert pipe_attrs["end_finish"].rule_id == "pipe_end_finish"

    # Bearing cage material
    brg_attrs = {a.key: a for a in extract_attributes("BEARING 6308 2RS C3 BRASS CAGE", "BEARING")}
    assert brg_attrs["cage_material"].value_text == "BRASS"
    assert brg_attrs["cage_material"].rule_id == "brg_cage"

    # Valve trim
    vlv_attrs = {a.key: a for a in extract_attributes("GLOBE VALVE 3 INCH CLASS 300 FLANGED WCB TRIM 8", "VALVE")}
    assert vlv_attrs["trim_material"].value_text == "TRIM_8"
    assert vlv_attrs["trim_material"].rule_id == "vlv_trim"

    # Gasket ring construction
    gskt_attrs = {a.key: a for a in extract_attributes("SPIRAL WOUND GASKET 2 INCH 150# CGI SS316 GRAPHITE", "GASKET")}
    assert gskt_attrs["ring_construction"].value_text == "CGI"
    assert gskt_attrs["ring_construction"].rule_id == "gskt_ring"

    # Cable flame rating
    cbl_attrs = {a.key: a for a in extract_attributes("CABLE 3.5C X 95 SQMM AL XLPE 1.1KV ARMOURED FRLS", "CABLE")}
    assert cbl_attrs["flame_rating"].value_text == "FRLS"
    assert cbl_attrs["flame_rating"].rule_id == "cbl_frls"


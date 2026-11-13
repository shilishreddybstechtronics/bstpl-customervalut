with open('backend/routes_data.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = """            else:
                cols = [Device.device_sr_no, Device.imei, Device.iccid, Device.msisdn1, Device.msisdn2, Customer.name,
                        Device.model, Device.sim_provider, Device.activation_plan, Device.firmware, Device.flash, Device.sim_type]
                sub_or = [c.like(like) for c in cols] + [
                    cast(Device.act_date, String).like(like),
                    cast(Device.dispatched_date, String).like(like),
                    cast(Device.expiry_date, String).like(like),
                    cast(Device.extra, String).like(like)
                ]
                if clean_part:
                    sub_or.append(Device.iccid.like(f"%{escape_like(clean_part)}%"))
                    stripped = clean_part.rstrip("F")
                    if stripped and stripped != clean_part:
                        sub_or.append(Device.iccid.like(f"%{escape_like(stripped)}%"))
                if dt_like:
                    sub_or.extend([
                        cast(Device.act_date, String).like(dt_like),
                        cast(Device.dispatched_date, String).like(dt_like),
                        cast(Device.expiry_date, String).like(dt_like)
                    ])
                term_filters.append(or_(*sub_or))"""

replacement = """            else:
                # Fast indexed search for IMEIs, serial numbers, phone numbers
                if part.isdigit() and len(part) >= 10:
                    sub_or = [
                        Device.imei == part,
                        Device.imei.like(like),
                        Device.iccid.like(like),
                        Device.device_sr_no.like(like),
                        Device.msisdn1.like(like),
                        Customer.name.like(like),
                    ]
                else:
                    cols = [Customer.name, Device.imei, Device.iccid, Device.device_sr_no, Device.msisdn1, Device.msisdn2,
                            Device.model, Device.sim_provider, Device.activation_plan, Device.firmware, Device.flash, Device.sim_type]
                    sub_or = [c.like(like) for c in cols]
                if clean_part:
                    sub_or.append(Device.iccid.like(f"%{escape_like(clean_part)}%"))
                    stripped = clean_part.rstrip("F")
                    if stripped and stripped != clean_part:
                        sub_or.append(Device.iccid.like(f"%{escape_like(stripped)}%"))
                if norm_dt:
                    sub_or.extend([
                        Device.act_date == norm_dt,
                        Device.dispatched_date == norm_dt,
                        Device.expiry_date == norm_dt
                    ])
                term_filters.append(or_(*sub_or))"""

if target in c:
    c = c.replace(target, replacement)
    with open('backend/routes_data.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("SUCCESS: Optimized backend/routes_data.py query!")
else:
    print("ERROR: target block not found in routes_data.py")


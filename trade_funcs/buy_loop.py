def buy_loop(pair,fix_trade_value=5000,margin=2,loop_duration=20):
    base_currency_precision = precision[f"{pair}INR"]['base_currency_precision']
    target_currency_precision = precision[f"{pair}INR"]['target_currency_precision']

    while True:
        # checking parameters
        with open('parameters.txt', 'r') as file:
            s = file.read()
        exec(s)

        cancal_all(pair, side='buy', market='INR')

        if run_buy_loop:
            try:
                inr_balance = check_balance('INR')
                inr_balance = inr_balance if inr_balance else 0
                coin_holding = get_coin_value(pair)

                # Buy Machine - Pause mechanism
                if coin_holding < fix_trade_value:
                    loop_val = fix_trade_value
                else :
                    loop_val = 2*fix_trade_value - coin_holding if (2*fix_trade_value - coin_holding)>=0 else 0

                inr_trade_value = min(loop_val,inr_balance*.9)


                if inr_trade_value > 200:
                    # aage badho
                    bids = scan_orderbook(pair)
                    # remove orders with amount < 500 inr
                    bids = bids[bids['value']>500].reset_index(drop=True)

                    # define max buy price
                    max_buy_price = get_max_buy_price(pair=pair,margin=margin,ignore_value=500)

                    # extract highest bid price
                    highest_bid_price = bids[bids['price'] < max_buy_price]['price'].values[0]

                    # get the buy price
                    buy_price = highest_bid_price + (1 / (10 ** base_currency_precision))

                    # calculate quantity to purchase
                    purchase_qty = round(inr_trade_value/buy_price,target_currency_precision)

                    timestamp = int(round(time.time()*1000))
                    # place purchase order
                    order_id = create_order(pair, price=buy_price, order_qty = purchase_qty,
                                                base_currency_precision = base_currency_precision,
                                                timestamp=timestamp ,side='buy',order_type ='limit_order')

                    # check status of this order
                    status_dict = check_order_status(order_id)


                    loop_start_time = time.time()
                    while True:
                        status_dict = check_order_status(order_id)
                        order_status = status_dict['status']
                        if order_status in ("init","open","partially_filled"):
                            # print('L1')
                            buy_logs.append(f"Placed a buy order at {buy_price} for {purchase_qty} coins successfully.")

                            # Check if someone placed an order above our buy order
                            bids = scan_orderbook(pair)
                            # remove orders with amount < 500 inr
                            bids = bids[bids['value']>500].reset_index(drop=True)

                            # print("L2")

                            # extract highest bid price
                            highest_bid_price = bids[bids['price'] < max_buy_price]['price'].values[0]
                            highest_bid_price_2 = bids[bids['price'] < max_buy_price]['price'].values[1]

                            if highest_bid_price > buy_price:
                                buy_price = highest_bid_price + (1 / (10 ** base_currency_precision))
                                status_dict = edit_order(order_id, buy_price)
                                # print("L3")

                                if status_dict['status'] == 'error':
                                    buy_logs.append(f'Error aa gayi edit ke status me: {status_dict}')
                                    break
                                else:
                                    buy_logs.append(f'''Edited:  Price:{status_dict['price_per_unit']}  Quantity:{status_dict['total_quantity']}''')

                            elif buy_price > highest_bid_price_2 * 1.0001:
                                # print("L4")
                                buy_price = highest_bid_price_2 + (1 / (10 ** base_currency_precision))
                                status_dict = edit_order(order_id,buy_price)

                                if status_dict['status'] == 'error':
                                    buy_logs.append(f'Error aa gayi edit ke status me\n {status_dict}')
                                    break
                                else:
                                    buy_logs.append(f'''Edited:  Price:{status_dict['price_per_unit']}  Quantity:{status_dict['total_quantity']}''')

                            else:
                                buy_logs.append('Still on top!')
                                # print('L5')
                                time.sleep(1)

                        elif order_status == "filled":
                            buy_logs.append("Order fulfilled.")
                            # print("L6")
                            # cancel whole order
                            # cancel_order(status_dict["id"])
                            break
                        elif order_status in ("partially_cancelled", "cancelled", "rejected"):
                            buy_logs.append("Failed to place buy order.")
                            # print("L7")
                            # cancel whole order
                            cancel_order(status_dict["id"])
                            break

                        time_elapsed = time.time() - loop_start_time
                        if time_elapsed > loop_duration:
                            buy_logs.append("Ho gya time out!")
                            # cancel whole order before breaking the loop
                            cancel_order(order_id)
                            break
                else:
                    buy_logs.append('put an amount grater than 100')
            except Exception as e:
                print(e)
        else:
            cancal_all(pair, side='buy', market='INR')
            break
